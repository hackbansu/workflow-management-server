from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model

from rest_framework.exceptions import ValidationError

User = get_user_model()


def filter_token(token):
    token, user_id = token.split('--')

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise ValidationError({'detail': 'invalid token'})

    if not default_token_generator.check_token(user, token):
        raise ValidationError({'detail': 'invalid token'})

    return (token, user)
