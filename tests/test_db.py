import pytest
from flask import Flask
from src.models import db, User

@pytest.fixture
def app():
    """
    Create a Flask app configured for testing with an in-memory SQLite DB.
    """
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "test_key"

    db.init_app(app)

    # Create all tables for a clean slate before each test session
    with app.app_context():
        db.create_all()

    yield app

    # Teardown: Drop all tables after test session
    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    """
    Provides a test client for sending requests to the Flask app (if needed).
    """
    return app.test_client()


def test_create_user(app):
    """
    Test that a User can be created and stored in the database.
    """
    with app.app_context():
        user = User(username="john_doe", email="john@example.com", password="secret")
        db.session.add(user)
        db.session.commit()

        # Query back
        stored_user = User.query.filter_by(username="john_doe").first()
        assert stored_user is not None
        assert stored_user.username == "john_doe"
        assert stored_user.email == "john@example.com"
        assert stored_user.password == "secret"
        assert stored_user.is_active is True  # default value


def test_repr_method(app):
    """
    Test the __repr__ method returns the correct string representation.
    """
    with app.app_context():
        user = User(username="jane_doe", email="jane@example.com", password="secret")
        db.session.add(user)
        db.session.commit()

        assert repr(user) == "User('jane_doe', 'jane@example.com')"


def test_unique_constraints(app):
    """
    Test that creating two users with the same username or email raises an error.
    """
    with app.app_context():
        user1 = User(username="duplicate", email="dup@example.com", password="pass1")
        db.session.add(user1)
        db.session.commit()

        # Attempt to insert another user with the same username
        user2 = User(username="duplicate", email="dup2@example.com", password="pass2")

        # Depending on your setup, you might get an IntegrityError from SQLAlchemy
        from sqlalchemy.exc import IntegrityError

        db.session.add(user2)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()  # Roll back so we can test the next unique constraint

        # Now test duplicate email
        user3 = User(username="unique_username", email="dup@example.com", password="pass3")
        db.session.add(user3)
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_is_active_default_true(app):
    """
    Test that 'is_active' column defaults to True if not specified.
    """
    with app.app_context():
        user = User(username="alice", email="alice@example.com", password="pass")
        db.session.add(user)
        db.session.commit()

        fetched = User.query.filter_by(username="alice").first()
        assert fetched is not None
        assert fetched.is_active is True


def test_update_user_is_active(app):
    """
    Test updating the is_active field for a user.
    """
    with app.app_context():
        user = User(username="bob", email="bob@example.com", password="pass", is_active=True)
        db.session.add(user)
        db.session.commit()

        fetched = User.query.filter_by(username="bob").first()
        fetched.is_active = False
        db.session.commit()

        updated = User.query.filter_by(username="bob").first()
        assert updated.is_active is False
