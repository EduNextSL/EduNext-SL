from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class ActiveUserJWTAuthentication(JWTAuthentication):
    """JWT auth that re-checks account state in the database on every request.

    Role and status are never read from the token, so suspending an account or
    changing its role takes effect immediately rather than when the token expires.
    """

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if not user.can_authenticate:
            raise AuthenticationFailed("User is inactive.", code="user_inactive")
        return user
