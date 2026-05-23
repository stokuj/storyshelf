import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def django_db_setup():
    pass


@pytest.fixture
def user(db):
    return User.objects.get_or_create(
        handle="testuser", defaults={"email": "testuser@test.com"}
    )[0]


@pytest.fixture
def admin_user(db):
    u, _ = User.objects.get_or_create(
        handle="admin_fixture",
        defaults={"email": "admin_fixture@test.com", "is_staff": True, "is_superuser": True},
    )
    u.is_staff = True
    u.is_superuser = True
    u.set_password("adminpass")
    u.save()
    return u


@pytest.fixture
def regular_user(db):
    u, _ = User.objects.get_or_create(
        handle="regular_fixture",
        defaults={"email": "regular_fixture@test.com"},
    )
    u.set_password("userpass")
    u.save()
    return u


@pytest.fixture
def book(db):
    from books.models import Book

    return Book.objects.create(title="Test Book", year=2020, page_count=100)


@pytest.fixture
def character_a(db, book):
    from analysis.models import BookCharacter

    return BookCharacter.objects.get_or_create(name="Frodo", book=book)[0]


@pytest.fixture
def character_b(db, book):
    from analysis.models import BookCharacter

    return BookCharacter.objects.get_or_create(name="Sam", book=book)[0]
