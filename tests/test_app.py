
import pytest
from app import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False
    )
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_home_page(client):
    response = client.get("/")
    assert response.status_code in (200, 302)


def test_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200


def test_invalid_login(client):
    response = client.post(
        "/login",
        data={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        },
        follow_redirects=True
    )
    assert response.status_code == 200
