from __future__ import unicode_literals
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password as django_password_validator

from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.compat import authenticate

from apps.common import constant as common_constant

User = get_user_model()

logger = logging.getLogger(__name__)


class BaseUserSerializer(serializers.ModelSerializer):
    '''
    Base user serializer, purpose to give only basic detail of user.
    '''

    profile_photo_url = serializers.URLField(
        source='profile_photo',
        read_only=True
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name',
                  'profile_photo', 'profile_photo_url')
        extra_kwargs = {
            'profile_photo': {
                'write_only': True,
            },
        }


class InviteUserSerializer(serializers.Serializer):
    '''
    Invite user to company with this serializer.
    '''
    email = serializers.EmailField(
        required=True,
        help_text='Email field, need to be unique, will be trated as username'
    )
    first_name = serializers.CharField(
        max_length=254,
        required=True,
        help_text='User\'s first name'
    )
    last_name = serializers.CharField(
        max_length=254,
        help_text='User\'s last name'
    )
    profile_photo = serializers.ImageField(
        help_text='User profile photo',
        required=False
    )


class CreateUserSerializer(BaseUserSerializer):
    '''
    Serializer use to create new user, used with the user company signup.
    '''
    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + ('email', 'id')
        extra_kwargs = BaseUserSerializer.Meta.extra_kwargs.copy()
        extra_kwargs = {
            'id': {
                'read_only': True
            }
        }


class UpdateUserSerializer(BaseUserSerializer):
    '''
    Update details of existing user, email cannot be updated. Also use for user retreival.
    '''
    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + ('email', 'id')
        extra_kwargs = BaseUserSerializer.Meta.extra_kwargs.copy()
        extra_kwargs.update({
            'id': {
                'help_text': 'User unique id',
                'read_only': True
            },
            'email': {
                'read_only': True
            }
        })


class UserDetailSerializer(UpdateUserSerializer):
    '''
    User Detail\'s email, id, token are extended.
    '''
    class Meta(UpdateUserSerializer.Meta):
        # Mark: Y not super
        fields = UpdateUserSerializer.Meta.fields + ('token',)
        extra_kwargs = UpdateUserSerializer.Meta.extra_kwargs.copy()
        extra_kwargs.update({
            'email': {
                'read_only': False
            },
            'token': {
                'help_text': 'User auth token',
                'read_only': True
            }
        })

    def validate_email(self, value):
        '''
        Validate user email, prevent email already registered error for updated same account.
        '''
        qs = User.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError(
                {'detail': 'This email is already registered with the system'})
        return value

    def create(self, validated_data):
        '''
        Create user, create vs create_user conflict.
        '''
        return User.objects.create_user(**validated_data)


class AuthTokenSerializer(serializers.Serializer):
    '''
    AuthTokenSerializer is use to authenticate user credentials and log it in.
    '''
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, attrs):
        '''
        Validate credentials.
        '''
        email = attrs['email']
        password = attrs['password']

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        # The authenticate call simply returns None for is_active=False
        # users.
        if not user:
            msg = {'detail': 'Unable to log in with provided credentials.'}
            raise serializers.ValidationError(msg, code='authorization')
        attrs['user'] = user
        return attrs

    def create(self, validated_data):
        '''
        login user.
        '''
        validated_data['user'].login_now()
        return validated_data['user']


class ResetPasswordRequestSerializer(serializers.Serializer):
    '''
    Reset password request handled with this.
    '''
    email = serializers.EmailField(required=True)

    def validate_email(self, email):
        '''
        verify incoming email.
        '''
        try:
            self.instance = User.objects.get(email__iexact=email)
            logger.debug('reset request for %s' % (self.instance))
        except User.DoesNotExist:
            self.instance = None
        return email


class ResetPasswordSerializer(UpdateUserSerializer):
    '''
    User password reset and token is invalidated.
    '''
    class Meta(UpdateUserSerializer.Meta):
        fields = ('password',)
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }

    def validate_password(self, password):
        if self.instance:
            django_password_validator(password=password, user=self.instance)
        return password

    def update(self, instance, validated_data):
        '''
        reset user password.
        '''

        instance.set_password(validated_data['password'])
        # if invited user then the account will now be operational.

        instance.is_active = True

        # logout user of all devices.
        try:
            instance.auth_token.delete()
        except Token.DoesNotExist:
            pass

        # update login time, also invalidate current token.
        instance.login_now()

        return instance


class UserBasicDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'name')
        read_only_fields = ('id', 'email', 'name')
