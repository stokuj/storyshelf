import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def django_db_setup():
    pass


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def book(db):
    from books.models import Book

    return Book.objects.create(title="Test Book")


@pytest.fixture
def character_a(db):
    from analysis.models import BookCharacter

    return BookCharacter.objects.create(name="Frodo")


@pytest.fixture
def character_b(db):
    from analysis.models import BookCharacter

    return BookCharacter.objects.create(name="Sam")
