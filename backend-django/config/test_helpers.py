from users.models import User


class AuthTestHelper:
    """Mixin that creates test users."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="user@test.com",
            handle="testuser",
            password="password123",
        )
