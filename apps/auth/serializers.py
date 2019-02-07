from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password as django_password_validator

from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.compat import authenticate

from apps.common import constant as common_constant

User = get_user_model()


class BaseUserSerializer(serializers.ModelSerializer):
    '''
    Base user serializer, purpose to give only basic detail of user.
    '''
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'profile_photo')
        extra_kwargs = {
            'last_name': {
                'help_text': 'User last name'
            },
            'first_name': {
                'required': True
            }
        }


class InviteUserSerializer(serializers.Serializer):
    '''
    Invite user to company with this serializer.
    '''
    email = serializers.EmailField(
        required=True, help_text='Email field, need to be unique, will be trated as username')
    first_name = serializers.CharField(
        max_length=254, required=True, help_text='User first name')
    last_name = serializers.CharField(
        max_length=254, help_text='User last name')
    profile_photo = serializers.ImageField(help_text='User profile photo')


class CreateUserSerializer(BaseUserSerializer):
    '''
    Serializer use to create new user, used with the user company signup.
    '''

    def validate_email(self, value):
        if self.instance:
            raise serializers.ValidationError(
                {'detail': 'email cannot be updated'})
        return value

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

    def validate_password(self, password):
        django_password_validator(password=password, user=self.instance)
        return password

    def update(self, instance, validated_data):
        '''
        Update user , override because of set_password.
        '''
        instance = super(UpdateUserSerializer, self).update(
            instance, validated_data
        )
        password = validated_data.get('password', None)

        if password:
            instance.set_password(password)

        instance.save()
        return instance

    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + ('password', 'email', 'id')
        extra_kwargs = BaseUserSerializer.Meta.extra_kwargs.copy()
        extra_kwargs.update({
            'password': {
                'write_only': True,
                'help_text': 'Password for the account.'
            },
            'id': {
                'help_text': 'User unique id',
                'read_only': True
            }
        })


class LoginUserSerializer(UpdateUserSerializer):
    '''
    Create new user. apart from UpdateUserSerializer email, id, token are added.
    '''

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

    class Meta(UpdateUserSerializer.Meta):
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
            User.objects.get(email=email)
        except User.DoesNotExist:
            pass
        return email


class ResetPasswordSerializer(UpdateUserSerializer):
    '''
    User password reset and token is invalidated.
    '''

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

    class Meta(UpdateUserSerializer.Meta):
        fields = ['password']
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }


class InvitationSerializer(ResetPasswordSerializer):
    '''
    Serializer to accept invitaion of user
    '''
    def update(self, instance, validated_data):
        '''
        Override to activate employee account.
        '''
        instance = super(InvitationSerializer, self).update(
            instance, validated_data)
        user_company = instance.user_companies.filter(
            status=common_constant.USER_STATUS.INVITED
        )
        if user_company.exists():
            user_company = user_company.first()
            user_company.status = common_constant.USER_STATUS.ACTIVE
            user_company.save()
        return instance
