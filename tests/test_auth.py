import pytest
from app import create_app
from models import db, User, CreatorProfile, BrandProfile

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_user_password_hashing(app):
    user = User(email='test@creatora.ai', role='creator')
    user.set_password('SecretPass123!')
    assert user.password_hash is not None
    assert user.check_password('SecretPass123!') is True
    assert user.check_password('WrongPass') is False

def test_user_roles(app):
    c = User(email='creator@creatora.ai', role='creator')
    b = User(email='brand@creatora.ai', role='brand')
    a = User(email='admin@creatora.ai', role='admin')
    assert c.is_creator is True
    assert b.is_brand is True
    assert a.is_admin is True

def test_home_page_loads(client):
    res = client.get('/')
    assert res.status_code == 200
    assert b'Creatora' in res.data
