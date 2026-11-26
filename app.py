import os
import secrets
import webbrowser
from threading import Timer
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps
from urllib.parse import urlencode
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, jsonify, g
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import or_, func
from config import Config
from models import db, User, Shop, Product, Order, OrderItem, Review
from intl import (LANGUAGES, DEFAULT_LANGUAGE, RTL_LANGUAGES, COUNTRIES, CATEGORIES,
                  resolve_language, translate, format_money, format_local)

APP_VERSION = "3.0.0"
LANG_COOKIE = "nearbuy_lang"

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please sign in to continue."
login_manager.session_protection = "strong"
app.config["VERSION"] = APP_VERSION


def _(text, **kwargs):
    """Translate a UI string into the language of the current request (English fallback)."""
    return translate(text, getattr(g, "lang", DEFAULT_LANGUAGE), **kwargs)


def money(amount, currency):
    return format_money(amount, currency, getattr(g, "lang", DEFAULT_LANGUAGE))


def country_name(code):
    return _(COUNTRIES.get(code, {}).get("name", code))


def localtime_filter(value, tz_name):
    return format_local(value, tz_name)


def lang_url(code):
    """Current page with ?lang=<code> set, so switching language keeps the user where they are."""
    args = request.args.to_dict()
    args.pop("csrf_token", None)
    args["lang"] = code
    return request.path + "?" + urlencode(args)


app.jinja_env.globals.update(_=_, money=money, country_name=country_name, lang_url=lang_url)
app.add_template_filter(localtime_filter, "localtime")


@login_manager.user_loader
def load_user(user_id):
    user = db.session.get(User, int(user_id))
    return user if user and user.is_active else None


def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return wrapped
    return decorator


def csrf_value():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


@app.before_request
def resolve_request_language():
    requested = request.args.get("lang")
    g.lang = resolve_language(
        requested,
        request.cookies.get(LANG_COOKIE),
        request.accept_languages.best_match(list(LANGUAGES)),
    )
    # An explicit ?lang= choice is remembered for a year.
    g.persist_lang = requested in LANGUAGES


@app.after_request
def remember_language(response):
    if getattr(g, "persist_lang", False):
        response.set_cookie(LANG_COOKIE, g.lang, max_age=60 * 60 * 24 * 365, samesite="Lax",
                            secure=app.config["SESSION_COOKIE_SECURE"])
    return response


@app.before_request
def protect_requests():
    # First launch is deliberately gated until the owner creates the admin account.
    if request.endpoint not in ("setup", "static", "health"):
        if not User.query.filter_by(role="admin").first():
            return redirect(url_for("setup"))
    if request.method == "POST":
        expected = session.get("_csrf_token")
        supplied = request.form.get("csrf_token", "")
        if not expected or not secrets.compare_digest(expected, supplied):
            abort(400, description=_("Security token expired. Refresh the page and try again."))


@app.context_processor
def inject_globals():
    cart = session.get("cart", {})
    return {
        "cart_count": sum(int(v) for v in cart.values()),
        "csrf_token": csrf_value,
        "app_version": app.config["VERSION"],
        "categories": CATEGORIES,
        "countries": COUNTRIES,
        "languages": LANGUAGES,
        "current_lang": g.lang,
        "direction": "rtl" if g.lang in RTL_LANGUAGES else "ltr",
    }


@app.after_request
def no_store_for_user_pages(response):
    # Carts, orders and dashboards are per-user; keep shared caches from storing them.
    if current_user.is_authenticated or session.get("cart"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response


@app.route("/")
def index():
    city = request.args.get("city", "Madurai").strip() or "Madurai"
    category = request.args.get("category", "").strip()
    q = request.args.get("q", "").strip()
    shops_query = Shop.query.filter_by(city=city, approved=True)
    if category:
        shops_query = shops_query.filter_by(category=category)
    if q:
        shops_query = shops_query.filter(or_(Shop.name.ilike(f"%{q}%"),
            Shop.category.ilike(f"%{q}%"), Shop.area.ilike(f"%{q}%"),
            Shop.description.ilike(f"%{q}%")))
    shops = shops_query.order_by(Shop.name).all()
    products_query = Product.query.join(Shop).filter(
        Shop.city == city, Shop.approved.is_(True), Product.active.is_(True))
    if q:
        products_query = products_query.filter(or_(Product.name.ilike(f"%{q}%"),
            Product.description.ilike(f"%{q}%")))
    products = products_query.limit(8).all()
    return render_template("index.html", city=city, shops=shops, products=products,
                           selected_category=category, q=q)


@app.route("/shops")
def shops():
    city = request.args.get("city", "Madurai").strip() or "Madurai"
    category = request.args.get("category", "")
    country = request.args.get("country", "").strip().upper()
    q = request.args.get("q", "").strip()
    query = Shop.query.filter_by(city=city, approved=True)
    if category:
        query = query.filter_by(category=category)
    if country in COUNTRIES:
        query = query.filter_by(country=country)
    if q:
        query = query.filter(or_(Shop.name.ilike(f"%{q}%"), Shop.area.ilike(f"%{q}%")))
    return render_template("shops.html", shops=query.order_by(Shop.name).all(),
                           city=city, category=category, country=country, q=q)


@app.route("/shop/<int:shop_id>")
def shop_detail(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    if not shop.approved:
        abort(404)
    products = Product.query.filter_by(shop_id=shop.id, active=True).all()
    avg = db.session.query(func.avg(Review.rating)).filter_by(shop_id=shop.id).scalar()
    return render_template("shop_detail.html", shop=shop, products=products,
                           average=round(float(avg), 1) if avg else None)


@app.route("/setup", methods=["GET", "POST"])
def setup():
    if User.query.filter_by(role="admin").first():
        return redirect(url_for("login"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if len(name) < 2 or "@" not in email or len(password) < 12:
            flash(_("Enter a name, valid email and a password of at least 12 characters."), "error")
        elif password != confirm:
            flash(_("The passwords do not match."), "error")
        elif User.query.filter_by(email=email).first():
            flash(_("That email address is already in use."), "error")
        else:
            admin = User(name=name, email=email, role="admin")
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            login_user(admin)
            session.permanent = True
            flash(_("Your NEARBUY administrator account is ready."), "success")
            return redirect(url_for("admin_dashboard"))
    return render_template("setup.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "customer")
        if role not in ("customer", "shopkeeper", "delivery"):
            role = "customer"
        if not name or not email or len(password) < 8:
            flash(_("Enter your name, email and a password with at least 8 characters."), "error")
        elif User.query.filter_by(email=email).first():
            flash(_("That email is already registered."), "error")
        else:
            user = User(name=name, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            session.permanent = True
            flash(_("Welcome to NEARBUY! Your account is ready."), "success")
            return redirect(url_for("dashboard"))
    return render_template("auth.html", mode="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(request.form.get("password", "")):
            login_user(user)
            session.permanent = True
            flash(_("Welcome back, {name}.", name=user.name), "success")
            return redirect(url_for("dashboard"))
        flash(_("Email or password is incorrect."), "error")
    return render_template("auth.html", mode="login")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash(_("You have been signed out."), "success")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "shopkeeper":
        shop = Shop.query.filter_by(phone=current_user.phone).first()
        if not shop:
            shop = Shop.query.filter_by(owner_name=current_user.name).first()
        return render_template("shop_dashboard.html", shop=shop)
    if current_user.role == "delivery":
        assigned = Order.query.filter_by(delivery_partner_id=current_user.id).order_by(Order.created_at.desc()).all()
        available = Order.query.filter_by(status="Ready for pickup", delivery_partner_id=None).all()
        return render_template("delivery_dashboard.html", assigned=assigned, available=available)
    if current_user.role == "admin":
        return redirect(url_for("admin_dashboard"))
    orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("customer_dashboard.html", orders=orders)


def _own_shop():
    return Shop.query.filter_by(owner_name=current_user.name, phone=current_user.phone).first()


@app.route("/shop/register", methods=["GET", "POST"])
@role_required("shopkeeper")
def shop_register():
    existing = _own_shop()
    if request.method == "POST":
        data = {k: request.form.get(k, "").strip() for k in
                ["name", "category", "description", "city", "area", "address", "phone"]}
        country = request.form.get("country", "").strip().upper()
        if existing and (existing.products or Order.query.filter_by(shop_id=existing.id).first()):
            # Prices are stored as numbers in the shop's currency; changing it afterwards would
            # silently re-label every existing price, so the country stays fixed once trading starts.
            country = existing.country
        if country not in COUNTRIES:
            country = "IN" if not existing else existing.country
            flash(_("Choose a country from the list."), "error")
        if not data["name"] or not data["category"] or not data["city"]:
            flash(_("Shop name, category and city are required."), "error")
        else:
            defaults = COUNTRIES[country]
            data.update(country=country, currency=defaults["currency"], timezone=defaults["timezone"])
            if existing:
                for k, v in data.items():
                    setattr(existing, k, v)
                existing.approved = False
                shop = existing
            else:
                shop = Shop(**data, owner_name=current_user.name, approved=False)
                db.session.add(shop)
            current_user.phone = data["phone"]
            db.session.commit()
            flash(_("Shop submitted for admin approval."), "success")
            return redirect(url_for("dashboard"))
    return render_template("shop_register.html", shop=existing)


@app.route("/shop/manage")
@role_required("shopkeeper")
def manage_shop():
    shop = _own_shop()
    if not shop:
        flash(_("Register your shop first."), "error")
        return redirect(url_for("shop_register"))
    products = Product.query.filter_by(shop_id=shop.id).all()
    orders = Order.query.filter_by(shop_id=shop.id).order_by(Order.created_at.desc()).all()
    return render_template("manage_shop.html", shop=shop, products=products, orders=orders)


@app.route("/shop/insights")
@role_required("shopkeeper")
def retail_insights():
    """Transparent, rules-based inventory and demand insights for the merchant."""
    shop = _own_shop()
    if not shop:
        flash(_("Register your shop first."), "error")
        return redirect(url_for("shop_register"))
    products = Product.query.filter_by(shop_id=shop.id, active=True).order_by(Product.name).all()
    since = datetime.utcnow() - timedelta(days=30)
    sales_rows = (db.session.query(OrderItem.product_id, func.sum(OrderItem.quantity),
                    func.sum(OrderItem.quantity * OrderItem.unit_price))
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.shop_id == shop.id, Order.created_at >= since,
                Order.status != "Cancelled", OrderItem.product_id.isnot(None))
        .group_by(OrderItem.product_id).all())
    sales = {pid: {"units": int(units or 0), "revenue": float(revenue or 0)}
             for pid, units, revenue in sales_rows}
    insights = []
    for product in products:
        sold = sales.get(product.id, {}).get("units", 0)
        daily = sold / 30.0
        cover = (product.stock / daily) if daily > 0 else None
        target = int(round(daily * 14))
        restock = max(0, target - product.stock)
        if product.stock <= 3:
            level, label = "critical", "Very low stock"
        elif cover is not None and cover < 7:
            level, label = "warning", "Likely to run low"
        elif sold == 0:
            level, label = "neutral", "No recorded sales"
        else:
            level, label = "healthy", "Stock looks healthy"
        insights.append({"product": product, "sold": sold,
            "revenue": sales.get(product.id, {}).get("revenue", 0),
            "daily": daily, "cover": cover, "restock": restock,
            "level": level, "label": label})
    insights.sort(key=lambda row: (0 if row["level"] == "critical" else 1 if row["level"] == "warning" else 2, -row["sold"], row["product"].name))
    total_units = sum(row["sold"] for row in insights)
    total_revenue = sum(row["revenue"] for row in insights)
    low_stock = sum(1 for row in insights if row["level"] in ("critical", "warning"))
    return render_template("retail_insights.html", shop=shop, insights=insights,
        total_units=total_units, total_revenue=total_revenue,
        low_stock=low_stock, period_start=since)


@app.route("/shop/product/<int:product_id>/stock", methods=["POST"])
@role_required("shopkeeper")
def update_product_stock(product_id):
    shop = _own_shop()
    product = Product.query.get_or_404(product_id)
    if not shop or product.shop_id != shop.id:
        abort(403)
    try:
        stock = int(request.form.get("stock", "-1"))
        if stock < 0 or stock > 1000000:
            raise ValueError()
        product.stock = stock
        db.session.commit()
        flash(_("Stock updated for {name}.", name=product.name), "success")
    except ValueError:
        flash(_("Enter a valid stock quantity."), "error")
    return redirect(url_for("retail_insights"))


@app.route("/shop/product/add", methods=["POST"])
@role_required("shopkeeper")
def add_product():
    shop = _own_shop()
    if not shop:
        return redirect(url_for("shop_register"))
    try:
        price = Decimal(request.form.get("price", "0"))
        stock = int(request.form.get("stock", "0"))
        name = request.form.get("name", "").strip()
        if price <= 0 or stock < 0 or not name or len(name) > 140:
            raise ValueError()
        if not shop.approved:
            raise ValueError()
        product = Product(shop_id=shop.id, name=name,
            description=request.form.get("description", "").strip(), price=price,
            stock=stock, unit=request.form.get("unit", "piece").strip()[:30] or "piece",
            image_emoji=request.form.get("emoji", "📦")[:12] or "📦")
        db.session.add(product)
        db.session.commit()
        flash(_("Product added."), "success")
    except (ValueError, KeyError, ArithmeticError):
        flash(_("Enter a valid product name, price and stock."), "error")
    return redirect(url_for("manage_shop"))


@app.route("/shop/order/<int:order_id>/status", methods=["POST"])
@role_required("shopkeeper")
def shop_order_status(order_id):
    shop = _own_shop()
    order = Order.query.get_or_404(order_id)
    if not shop or order.shop_id != shop.id:
        abort(403)
    status = request.form.get("status")
    if status in ("Confirmed", "Preparing", "Ready for pickup"):
        order.status = status
        db.session.commit()
        flash(_("Order status updated."), "success")
    return redirect(url_for("manage_shop"))


@app.route("/cart/add/<int:product_id>", methods=["POST"])
def cart_add(product_id):
    product = Product.query.get_or_404(product_id)
    if not product.active or product.stock < 1:
        flash(_("This product is currently unavailable."), "error")
    else:
        cart = session.get("cart", {})
        key = str(product_id)
        cart[key] = min(int(cart.get(key, 0)) + 1, product.stock)
        session["cart"] = cart
        flash(_("{name} added to your cart.", name=product.name), "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/cart")
def cart():
    cart_data = session.get("cart", {})
    items = []
    totals = {}          # one total per currency: never add ₹ to $
    shop_ids = set()
    for pid, qty in cart_data.items():
        product = db.session.get(Product, int(pid))
        if product and product.active:
            line = product.price * int(qty)
            items.append({"product": product, "qty": int(qty), "line": line})
            currency = product.shop.currency
            totals[currency] = totals.get(currency, Decimal("0.00")) + line
            shop_ids.add(product.shop_id)
    return render_template("cart.html", items=items, totals=totals, shop_count=len(shop_ids))


@app.route("/cart/update", methods=["POST"])
def cart_update():
    cart_data = session.get("cart", {})
    for pid in list(cart_data):
        try:
            qty = int(request.form.get(pid, "0"))
            product = db.session.get(Product, int(pid))
            if qty <= 0 or not product:
                cart_data.pop(pid, None)
            else:
                cart_data[pid] = min(qty, product.stock)
        except ValueError:
            cart_data.pop(pid, None)
    session["cart"] = cart_data
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart_data = session.get("cart", {})
    if not cart_data:
        flash(_("Your cart is empty."), "error")
        return redirect(url_for("cart"))
    lines = []
    for pid, qty in cart_data.items():
        p = db.session.get(Product, int(pid))
        if p and p.active and p.stock >= int(qty):
            lines.append((p, int(qty)))
    if not lines:
        flash(_("Your cart items are no longer available."), "error")
        return redirect(url_for("cart"))
    shops_in_cart = {p.shop_id for p, q in lines}
    if len(shops_in_cart) > 1:
        flash(_("For this prototype, checkout is limited to one shop per order. Place separate orders for different shops."), "error")
        return redirect(url_for("cart"))
    shop = lines[0][0].shop
    total = sum((p.price * q for p, q in lines), Decimal("0.00"))
    if request.method == "POST":
        address = request.form.get("address", "").strip()
        phone = request.form.get("phone", "").strip()
        if not address:
            flash(_("Please enter a delivery address."), "error")
        else:
            for product, quantity in lines:
                db.session.refresh(product)
                if not product.active or product.stock < quantity:
                    db.session.rollback()
                    flash(_("{name} no longer has enough stock. Please update your cart.", name=product.name), "error")
                    return redirect(url_for("cart"))
            order = Order(customer_id=current_user.id, shop_id=shop.id,
                customer_name=current_user.name, phone=phone,
                delivery_address=address, city=shop.city, total=total,
                currency=shop.currency, timezone=shop.timezone,
                payment_method="Demo / cash on delivery")
            db.session.add(order)
            db.session.flush()
            for p, qty in lines:
                db.session.add(OrderItem(order_id=order.id, product_id=p.id,
                    product_name=p.name, quantity=qty, unit_price=p.price))
                p.stock -= qty
            db.session.commit()
            session["cart"] = {}
            flash(_("Order #{id} placed successfully!", id=order.id), "success")
            return redirect(url_for("dashboard"))
    return render_template("checkout.html", lines=lines, total=total, currency=shop.currency)


@app.route("/delivery/claim/<int:order_id>", methods=["POST"])
@role_required("delivery")
def claim_delivery(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status == "Ready for pickup" and not order.delivery_partner_id:
        order.delivery_partner_id = current_user.id
        order.status = "Out for delivery"
        db.session.commit()
        flash(_("Delivery assigned to you."), "success")
    else:
        flash(_("This delivery is no longer available."), "error")
    return redirect(url_for("dashboard"))


@app.route("/delivery/status/<int:order_id>", methods=["POST"])
@role_required("delivery")
def delivery_status(order_id):
    order = Order.query.get_or_404(order_id)
    if order.delivery_partner_id != current_user.id:
        abort(403)
    status = request.form.get("status")
    if status in ("Out for delivery", "Delivered") and (status != "Delivered" or order.status == "Out for delivery"):
        order.status = status
        db.session.commit()
        flash(_("Delivery status updated."), "success")
    return redirect(url_for("dashboard"))


@app.route("/admin")
@role_required("admin")
def admin_dashboard():
    # Sum delivered value per currency. Adding INR and USD together would be meaningless.
    revenue_rows = (db.session.query(Order.currency, func.sum(Order.total))
                    .filter(Order.status == "Delivered").group_by(Order.currency).all())
    return render_template("admin_dashboard.html",
        shops=Shop.query.order_by(Shop.created_at.desc()).all(),
        orders=Order.query.order_by(Order.created_at.desc()).limit(30).all(),
        users_count=User.query.count(), products_count=Product.query.count(),
        orders_count=Order.query.count(),
        revenue={cur: total or 0 for cur, total in revenue_rows})


@app.route("/admin/shop/<int:shop_id>/approve", methods=["POST"])
@role_required("admin")
def approve_shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    shop.approved = True
    db.session.commit()
    flash(_("{name} approved.", name=shop.name), "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/order/<int:order_id>/status", methods=["POST"])
@role_required("admin")
def admin_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    status = request.form.get("status")
    if status in ("Placed", "Confirmed", "Preparing", "Ready for pickup", "Out for delivery", "Delivered", "Cancelled"):
        order.status = status
        db.session.commit()
    return redirect(url_for("admin_dashboard"))


@app.route("/ai-search")
def ai_search():
    # Transparent demo assistant: keyword-based matching, ready to connect to an LLM later.
    q = request.args.get("q", "").strip()
    city = request.args.get("city", "Madurai").strip()
    terms = [t for t in q.lower().split() if len(t) > 2]
    query = Product.query.join(Shop).filter(Shop.city == city, Shop.approved.is_(True), Product.active.is_(True))
    if terms:
        clauses = [Product.name.ilike(f"%{t}%") | Product.description.ilike(f"%{t}%") |
                   Shop.category.ilike(f"%{t}%") for t in terms]
        query = query.filter(or_(*clauses))
    results = query.limit(20).all()
    return render_template("ai_search.html", q=q, city=city, results=results)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "app": "NEARBUY", "version": app.config["VERSION"],
                    "setup_required": not bool(User.query.filter_by(role="admin").first())})


@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code=403, message=_("You do not have permission to view this page.")), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message=_("We couldn't find that page.")), 404


def seed_demo():
    # Demo marketplace listings are optional starter content; NO default admin or demo
    # passwords are created. The first-run setup screen creates the real owner account.
    if Shop.query.first():
        return
    sample_shops = [
        Shop(name="Meenakshi Fresh Mart", owner_name="Sample owner", category="Groceries", description="Daily essentials, fresh vegetables and pantry staples.", city="Madurai", area="Anna Nagar", address="Anna Nagar, Madurai", phone=""),
        Shop(name="Vaigai Furniture House", owner_name="Sample owner", category="Furniture", description="Practical furniture for homes, hostels and offices.", city="Madurai", area="KK Nagar", address="KK Nagar, Madurai", phone=""),
        Shop(name="Madurai Fresh Cuts", owner_name="Sample owner", category="Meat & Seafood", description="Fresh cuts with hygienic handling. Demo catalogue only.", city="Madurai", area="Goripalayam", address="Goripalayam, Madurai", phone=""),
        Shop(name="Pixel Point Electronics", owner_name="Sample owner", category="Electronics", description="Accessories and everyday electronics.", city="Madurai", area="Tallakulam", address="Tallakulam, Madurai", phone=""),
        Shop(name="South Street Hardware", owner_name="Sample owner", category="Hardware", description="Tools, fittings and home repair essentials.", city="Madurai", area="Bypass Road", address="Bypass Road, Madurai", phone=""),
        Shop(name="Cotton Lane", owner_name="Sample owner", category="Clothing", description="Everyday clothing and local styles.", city="Madurai", area="Town Hall Road", address="Town Hall Road, Madurai", phone=""),
    ]
    db.session.add_all(sample_shops)
    db.session.flush()
    catalog = [(0,"Basmati Rice","Premium rice · 1 kg",115,40,"kg","🍚"),(0,"Tomatoes","Farm-fresh tomatoes · 1 kg",32,60,"kg","🍅"),(0,"Cold-Pressed Groundnut Oil","Traditional cooking oil · 1 L",185,25,"litre","🫙"),(1,"Study Table","Engineered wood · compact design",3499,8,"piece","🪑"),(1,"Bookshelf","Four-tier storage shelf",2299,6,"piece","🗄️"),(1,"Dining Chair","Solid wood finish",1599,12,"piece","🪑"),(2,"Chicken Curry Cut","Fresh chicken · 500 g (demo listing)",145,20,"pack","🍗"),(2,"Mutton Curry Cut","Fresh mutton · 500 g (demo listing)",420,12,"pack","🥩"),(3,"Wireless Mouse","2.4 GHz USB mouse",499,18,"piece","🖱️"),(3,"USB-C Cable","Fast charging cable",249,30,"piece","🔌"),(4,"Tool Kit","Home repair starter kit",899,10,"kit","🧰"),(5,"Cotton Kurta","Everyday cotton wear",799,15,"piece","👕")]
    for si, name, desc, price, stock, unit, emoji in catalog:
        db.session.add(Product(shop_id=sample_shops[si].id, name=name, description=desc,
                               price=Decimal(str(price)), stock=stock, unit=unit, image_emoji=emoji))
    db.session.commit()


def upgrade_legacy_schema():
    """Additive, idempotent column migration for databases created by earlier releases.

    SQLAlchemy's create_all() never alters existing tables, so new columns are added here.
    Every new column has a default that matches the pilot (India / INR / Asia/Kolkata), so
    existing records keep their meaning. Back up the database before upgrading.
    """
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    preparer = db.engine.dialect.identifier_preparer
    additions = {
        "user": [("is_active", "BOOLEAN NOT NULL DEFAULT 1")],
        "shop": [("country", "VARCHAR(2) NOT NULL DEFAULT 'IN'"),
                 ("currency", "VARCHAR(3) NOT NULL DEFAULT 'INR'"),
                 ("timezone", "VARCHAR(60) NOT NULL DEFAULT 'Asia/Kolkata'")],
        # "order" is a reserved word in SQL, so the table name must be quoted.
        "order": [("currency", "VARCHAR(3) NOT NULL DEFAULT 'INR'"),
                  ("timezone", "VARCHAR(60) NOT NULL DEFAULT 'Asia/Kolkata'")],
    }
    tables = set(inspector.get_table_names())
    for table, columns in additions.items():
        if table not in tables:
            continue
        present = {column["name"] for column in inspector.get_columns(table)}
        for name, ddl in columns:
            if name not in present:
                db.session.execute(text(f"ALTER TABLE {preparer.quote(table)} ADD COLUMN {name} {ddl}"))
    db.session.commit()


with app.app_context():
    db.create_all()
    upgrade_legacy_schema()
    seed_demo()


if __name__ == "__main__":
    from waitress import serve
    host = os.getenv("NEARBUY_HOST", "127.0.0.1")
    port = int(os.getenv("NEARBUY_PORT", "5000"))
    if os.getenv("NEARBUY_OPEN_BROWSER", "1") == "1":
        Timer(1.2, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    print(f"NEARBUY {app.config['VERSION']} running at http://{host}:{port}")
    serve(app, host=host, port=port, threads=8)
