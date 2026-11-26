from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30), default="")
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="customer")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(60), nullable=False)
    description = db.Column(db.Text, default="")
    city = db.Column(db.String(80), nullable=False, index=True)
    area = db.Column(db.String(100), default="")
    address = db.Column(db.String(255), default="")
    phone = db.Column(db.String(30), default="")
    country = db.Column(db.String(2), nullable=False, default="IN")
    currency = db.Column(db.String(3), nullable=False, default="INR")
    timezone = db.Column(db.String(60), nullable=False, default="Asia/Kolkata")
    approved = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    products = db.relationship("Product", backref="shop", cascade="all, delete-orphan")

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shop.id"), nullable=False)
    name = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, default="")
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(30), default="piece")
    image_emoji = db.Column(db.String(12), default="📦")
    active = db.Column(db.Boolean, default=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey("shop.id"), nullable=False)
    delivery_partner_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    customer_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(30), default="")
    delivery_address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(30), default="Placed")
    payment_method = db.Column(db.String(30), default="Cash on delivery")
    currency = db.Column(db.String(3), nullable=False, default="INR")
    timezone = db.Column(db.String(60), nullable=False, default="Asia/Kolkata")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan")
    shop = db.relationship("Shop")

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    product_name = db.Column(db.String(140), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey("shop.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(500), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
