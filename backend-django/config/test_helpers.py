from users.models import User


class AuthTestHelper:
    """Mixin that creates test users with different roles."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="user@test.com",
            username="testuser",
            password="password123",
        )
        cls.admin = User.objects.create_user(
            email="admin@test.com",
            username="admin",
            password="password123",
            role="ADMIN",
        )
