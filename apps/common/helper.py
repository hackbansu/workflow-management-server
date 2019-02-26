import csv
from datetime import date

from django.conf import settings
from django.utils import six
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import base36_to_int, int_to_base36
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model

from rest_framework.exceptions import NotFound


User = get_user_model()


class InviteToken(object):
    '''
    Invite user token generator.
    '''
    key_salt = "django.contrib.auth.tokens.PasswordResetTokenGenerator"

    def make_token(self, user, employee):
        """
        Returns a token that can be used once to do a password reset
        for the given user.
        """
        return self._make_token_with_timestamp(user, self._num_days(self._today()), employee)

    def check_token(self, user, employee, token):
        """
        Check that a password reset token is correct for a given user.
        """
        if not (user and token):
            return False
        # Parse the token
        try:
            ts_b36, hash = token.split("-")
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        if not constant_time_compare(self._make_token_with_timestamp(user, ts, employee), token):
            return False

        # Check the timestamp is within limit
        if (self._num_days(self._today()) - ts) > settings.PASSWORD_RESET_TIMEOUT_DAYS:
            return False

        return True

    def _make_token_with_timestamp(self, user, timestamp, employee):
        # timestamp is number of days since 2001-1-1.  Converted to
        # base 36, this gives us a 3 digit string until about 2121
        ts_b36 = int_to_base36(timestamp)

        # By hashing on the internal state of the user and using state
        # that is sure to change (the password salt will change as soon as
        # the password is set, at least for current Django auth, and
        # last_login will also change), we produce a hash that will be
        # invalid as soon as it is used.
        # We limit the hash to 20 chars to keep URL short

        hash = salted_hmac(
            self.key_salt,
            self._make_hash_value(user, timestamp, employee),
        ).hexdigest()[::2]
        return "%s-%s" % (ts_b36, hash)

    def _make_hash_value(self, user, timestamp, employee):
        login_timestamp = '' if user.last_login is None else user.last_login.replace(
            microsecond=0, tzinfo=None)
        return (
            six.text_type(user.pk) + user.password +
            six.text_type(login_timestamp) +
            six.text_type(timestamp) + six.text_type(employee.pk)
        )

    def _num_days(self, dt):
        return (dt - date(2001, 1, 1)).days

    def _today(self):
        return date.today()


def filter_reset_password_token(token):
    token, user_id = token.split('--')

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise NotFound({'detail': 'invalid token'})

    if not default_token_generator.check_token(user, token):
        raise NotFound({'detail': 'invalid token'})

    return (token, user)


def filter_invite_token(token):
    token, user_id, employee_id = token.split('--')

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise NotFound({'detail': 'invalid token'})

    employee = user.user_companies.filter(pk=employee_id)
    if not employee.exists():
        raise NotFound({'detail': 'invalid token'})
    employee = employee.first()

    if not invite_token_generator.check_token(user, employee, token):
        raise NotFound({'detail': 'invalid token'})

    return (token, user, employee)


invite_token_generator = InviteToken()


def parse_invite_csv(file):
    data = []
    reader = csv.DictReader(file, delimiter=',')
    for row in reader:
        try:
            data.append({
                'user': {
                    'email': row['email'],
                    'first_name': row['first name'],
                    'last_name': row['last name']
                },
                'designation': row['designation']
            })
        except KeyError:
            return None

    return data


def generate_error(error_msg):
    return {'detail': error_msg}
