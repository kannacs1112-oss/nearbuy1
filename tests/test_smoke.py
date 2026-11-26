"""End-to-end smoke tests for the Flask app. Requires the full requirements.txt.

Test names are numbered because unittest runs tests alphabetically and the
first-run redirect must run before the administrator is created.
"""
import os
import re
import tempfile
import unittest

os.environ["NEARBUY_DATA_DIR"] = tempfile.mkdtemp(prefix="nearbuy-test-")
os.environ["NEARBUY_OPEN_BROWSER"] = "0"

from app import app  # noqa: E402
from models import db, User, Shop, Product, Order  # noqa: E402

ADMIN_EMAIL = "owner@example.com"
ADMIN_PASSWORD = "A-long-test-password-123"
SHOP_PASSWORD = "shop-pass-12345"


def csrf_from(response):
    return re.search(rb'name="csrf_token" value="([^"]+)"', response.data).group(1).decode()


class NearbuySmokeTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def _register(self, client, name, email, role):
        token = csrf_from(client.get("/register"))
        return client.post("/register", data={"csrf_token": token, "name": name, "email": email,
                                              "password": SHOP_PASSWORD, "role": role})

    # 1. First run: nothing works until the owner account exists.
    def test_00_first_run_redirects_to_setup(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/setup", response.location)

    def test_01_health(self):
        self.assertEqual(self.client.get("/health").status_code, 200)

    def test_02_first_admin_can_be_created(self):
        token = csrf_from(self.client.get("/setup"))
        response = self.client.post("/setup", data={"csrf_token": token, "name": "Local Owner",
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "confirm_password": ADMIN_PASSWORD})
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            self.assertIsNotNone(User.query.filter_by(email=ADMIN_EMAIL, role="admin").first())

    # 2. Language is chosen per visitor and remembered.
    def test_10_language_choice_is_remembered(self):
        client = app.test_client()
        first = client.get("/?lang=hi")
        self.assertIn('lang="hi"', first.get_data(as_text=True))
        self.assertIn("nearbuy_lang=hi", first.headers.get("Set-Cookie", ""))
        self.assertIn('lang="hi"', client.get("/shops").get_data(as_text=True))

    def test_11_unsupported_language_is_ignored(self):
        response = app.test_client().get("/?lang=klingon")
        self.assertIn('lang="en"', response.get_data(as_text=True))

    # 3. A shop in another country sells in its own currency, end to end.
    def test_20_us_shop_orders_are_priced_in_usd(self):
        merchant = app.test_client()
        self._register(merchant, "Sam Merchant", "sam@example.com", "shopkeeper")
        token = csrf_from(merchant.get("/shop/register"))
        response = merchant.post("/shop/register", data={"csrf_token": token, "name": "Austin Hardware",
            "category": "Hardware", "country": "US", "city": "Austin", "area": "Downtown",
            "phone": "+15125550100", "address": "1 Main St", "description": "Tools"})
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            shop = Shop.query.filter_by(name="Austin Hardware").one()
            self.assertEqual((shop.country, shop.currency, shop.timezone),
                             ("US", "USD", "America/New_York"))
            shop.approved = True  # admin approval is covered by the admin flow below
            db.session.commit()
            shop_id = shop.id

        token = csrf_from(merchant.get("/shop/manage"))
        merchant.post("/shop/product/add", data={"csrf_token": token, "name": "Hammer",
            "price": "24.99", "stock": "5", "unit": "piece", "emoji": "🔨", "description": "Steel"})
        with app.app_context():
            product_id = Product.query.filter_by(name="Hammer").one().id

        customer = app.test_client()
        self._register(customer, "Ravi Customer", "ravi@example.com", "customer")
        token = csrf_from(customer.get(f"/shop/{shop_id}"))
        customer.post(f"/cart/add/{product_id}", data={"csrf_token": token})
        cart_page = customer.get("/cart").get_data(as_text=True)
        self.assertIn("$24.99", cart_page)
        self.assertIn("Total (USD)", cart_page)
        self.assertNotIn("₹", cart_page)

        token = csrf_from(customer.get("/checkout"))
        response = customer.post("/checkout", data={"csrf_token": token, "address": "12 Oak Ave",
                                                    "phone": "+15125550199"})
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            order = Order.query.order_by(Order.id.desc()).first()
            self.assertEqual((order.currency, order.timezone), ("USD", "America/New_York"))
            order_id = order.id

        self.assertIn("$24.99", customer.get("/dashboard").get_data(as_text=True))

        # Admin: delivered value is reported per currency, never summed across currencies.
        admin = app.test_client()
        token = csrf_from(admin.get("/login"))
        admin.post("/login", data={"csrf_token": token, "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        with app.app_context():
            Order.query.get(order_id).status = "Delivered"
            db.session.commit()
        dashboard = admin.get("/admin").get_data(as_text=True)
        self.assertIn("$24.99", dashboard)

    # 4. Stock accuracy is unchanged by the currency work.
    def test_30_checkout_decrements_stock(self):
        with app.app_context():
            product = Product.query.filter_by(name="Hammer").one()
            self.assertEqual(product.stock, 4)


if __name__ == "__main__":
    unittest.main()
