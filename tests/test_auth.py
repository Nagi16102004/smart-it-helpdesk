import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import app, db


@pytest.fixture
def client():
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


def test_register_new_user(client):
    response = client.post('/register', data={
        'name': 'Test User',
        'email': 'newuser@test.com',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Registration successful' in response.data


def test_register_with_short_password_fails(client):
    response = client.post('/register', data={
        'name': 'Test User',
        'email': 'shortpass@test.com',
        'password': '123'
    }, follow_redirects=True)
    assert b'Password must be at least 6 characters long' in response.data


def test_login_with_wrong_password_fails(client):
    client.post('/register', data={
        'name': 'Test User',
        'email': 'loginuser@test.com',
        'password': 'password123'
    })
    response = client.post('/login', data={
        'email': 'loginuser@test.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert b'Invalid email or password' in response.data


def test_dashboard_requires_login(client):
    response = client.get('/dashboard', follow_redirects=True)
    assert b'Please login first' in response.data