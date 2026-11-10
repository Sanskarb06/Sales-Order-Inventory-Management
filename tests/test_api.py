
import pytest

from app import create_app, db
from app.models import User, Customer, Product, SalesOrder


@pytest.fixture
def api_app():
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "SECRET_KEY": "test-secret-key"
    })

    with app.app_context():
        db.create_all()

        admin = User(
            name="Test Admin",
            email="admin@test.com",
            role="Admin"
        )
        admin.set_password("testpassword")

        sales_user = User(
            name="Test Sales User",
            email="sales@test.com",
            role="Sales User"
        )
        sales_user.set_password("testpassword")

        customer = Customer(
            name="Test Customer",
            email="customer@test.com",
            status="Active"
        )

        product = Product(
            product_code="TEST-001",
            name="Test Keyboard",
            category="Electronics",
            price=1000,
            stock_quantity=20,
            status="Active"
        )

        db.session.add_all([
            admin, sales_user, customer, product
        ])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def api_client(api_app):
    with api_app.app_context():
        admin = User.query.filter_by(email="admin@test.com").first()
        admin_id = admin.id

    client = api_app.test_client()

    with client.session_transaction() as session:
        session["_user_id"] = str(admin_id)
        session["_fresh"] = True

    return client


def login_as(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def create_test_order(app, created_by):
    with app.app_context():
        order = SalesOrder(
            order_number="SO-TEST-001",
            customer_id=1,
            created_by=created_by,
            status="Draft",
            discount_percentage=0,
            subtotal=1000,
            discount_amount=0,
            grand_total=1000
        )

        db.session.add(order)
        db.session.commit()

        return order.id


def test_api_products(api_client):
    response = api_client.get("/api/products")

    assert response.status_code == 200

    data = response.get_json()
    assert "products" in data
    assert len(data["products"]) == 1


def test_api_create_order(api_app, api_client):
    response = api_client.post(
        "/api/orders",
        json={
            "customer_id": 1,
            "discount_percentage": 0,
            "items": [
                {
                    "product_id": 1,
                    "quantity": 2
                }
            ]
        }
    )

    assert response.status_code == 201

    data = response.get_json()
    assert data["order"]["status"] == "Draft"
    assert data["order"]["grand_total"] == "2000.00"

    with api_app.app_context():
        product = Product.query.first()
        assert product.stock_quantity == 20


def test_api_get_orders(api_client):
    response = api_client.get(
        "/api/orders?page=1&per_page=10"
    )

    assert response.status_code == 200

    data = response.get_json()
    assert "orders" in data
    assert "pagination" in data


def test_api_invalid_pagination(api_client):
    response = api_client.get(
        "/api/orders?page=0&per_page=10"
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "Invalid pagination parameters."
    )


def test_api_requires_login(api_app):
    client = api_app.test_client()

    response = client.get("/api/products")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_sales_user_can_access_own_order(api_app):
    with api_app.app_context():
        sales_user = User.query.filter_by(
            email="sales@test.com"
        ).first()
        sales_user_id = sales_user.id

    order_id = create_test_order(api_app, sales_user_id)

    client = api_app.test_client()
    login_as(client, sales_user_id)

    response = client.get(f"/api/orders/{order_id}")

    assert response.status_code == 200
    assert response.get_json()["order"]["id"] == order_id


def test_sales_user_cannot_access_another_users_order(api_app):
    with api_app.app_context():
        admin = User.query.filter_by(
            email="admin@test.com"
        ).first()
        sales_user = User.query.filter_by(
            email="sales@test.com"
        ).first()

        admin_id = admin.id
        sales_user_id = sales_user.id

    order_id = create_test_order(api_app, admin_id)

    client = api_app.test_client()
    login_as(client, sales_user_id)

    response = client.get(f"/api/orders/{order_id}")

    assert response.status_code == 403


def test_admin_can_access_another_users_order(api_app):
    with api_app.app_context():
        sales_user = User.query.filter_by(
            email="sales@test.com"
        ).first()
        sales_user_id = sales_user.id

    order_id = create_test_order(api_app, sales_user_id)

    client = api_app.test_client()

    with api_app.app_context():
        admin = User.query.filter_by(
            email="admin@test.com"
        ).first()
        admin_id = admin.id

    login_as(client, admin_id)

    response = client.get(f"/api/orders/{order_id}")

    assert response.status_code == 200

@pytest.mark.parametrize(
    "quantity",
    [0, -1, 1.5, True, False]
)
def test_api_rejects_invalid_quantity(api_client, quantity):
    response = api_client.post(
        "/api/orders",
        json={
            "customer_id": 1,
            "discount_percentage": 0,
            "items": [
                {
                    "product_id": 1,
                    "quantity": quantity
                }
            ]
        }
    )

    assert response.status_code == 400
