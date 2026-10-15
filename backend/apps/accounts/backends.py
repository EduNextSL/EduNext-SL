from django.contrib.auth.backends import ModelBackend


class ActiveAccountBackend(ModelBackend):
    """Email/password backend that also refuses suspended, disabled and pending accounts."""

    def user_can_authenticate(self, user):
        return super().user_can_authenticate(user) and user.can_authenticate
