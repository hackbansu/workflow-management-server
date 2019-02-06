from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.compat import authenticate

User = get_user_model()


class BaseUserSerializer(serializers.ModelSerializer):
    '''
    Base user serializer, purpose to give only basic detail of user.
    '''
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'profile_photo')
        extra_kwargs = {
            'first_name': {
                'help_text': 'User first name'
            },
            'last_name': {
                'help_text': 'User last name'
            },
            'profile_photo': {
                'help_text': 'User profile photo',
                'required': False
            },
        }


class InviteUserSerializer(serializers.Serializer):
    '''
    Invite user to company with this serializer.
    '''
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=254)
    last_name = serializers.CharField(required=False, max_length=254)
    profile_photo = serializers.ImageField(required=False)

    class Meta:
        extra_kwargs = {
            'email': {
                'help_text': 'Email field, need to be unique, will be trated as username, required'
            },
            'first_name': {
                'help_text': 'User first name'
            },
            'last_name': {
                'help_text': 'User last name'
            },
            'profile_photo': {
                'help_text': 'User profile photo',
                'required': False
            },
        }


class UpdateUserSerializer(BaseUserSerializer):
    '''
    Update details of existing user, email cannot be updated.
    '''

    def update(self, instance, validated_data):
        '''
        Update user , override because of set_password.
        '''
        instance = super(UpdateUserSerializer, self).update(
            instance, validated_data)
        password = validated_data.get('password', None)

        if password:
            instance.set_password(password)

        instance.save()
        return instance

    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + ('password',)
        extra_kwargs = BaseUserSerializer.Meta.extra_kwargs.copy()
        extra_kwargs.update({
            'password': {
                'write_only': True,
                'help_text': 'Password for the account, required'
            },
        })


class UserSerializer(UpdateUserSerializer):
    '''
    Create new user. apart from UpdateUserSerializer password, id, token are added.
    '''

    def validate_email(self, value):
        '''
        Validate user email, prevent email already registered error for updated same account..
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
        fields = UpdateUserSerializer.Meta.fields + ('email', 'id', 'token')
        extra_kwargs = UpdateUserSerializer.Meta.extra_kwargs.copy()
        extra_kwargs.update({
            'email': {
                'help_text': 'Email field, need to be unique, will be trated as username, required'
            }
        })


class AuthTokenSerializer(serializers.Serializer):
    '''
    AuthTokenSerializer is use to authenticate user credentials and log it in.
    '''
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        '''
        Validate credentials.
        '''
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
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
        else:
            msg = {'detail': 'Must include "email" and "password".'}
            raise serializers.ValidationError(msg, code='authorization')
        return attrs

    def create(self, validated_data):
        '''
        login user.
        '''
        user = User.objects.get(email=validated_data['email'])
        user.login_now()
        return user


class ResetTokenSerializer(serializers.Serializer):
    '''
    Reset password request handled with this.
    '''
    email = serializers.EmailField()

    def validate(self, attrs):
        '''
        verify incoming email.
        '''
        email = attrs.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                attrs['user'] = user
            except User.DoesNotExist:
                pass
        return attrs

    def create(self, validated_data):
        '''
        Send reset password request
        '''
        validated_data['user'].reset_password()
        return validated_data['user']


class ResetPasswordSerializer(serializers.ModelSerializer):
    '''
    User password reset and token is invalidated.
    '''

    def create(self, validated_data):
        '''
        reset user password.
        '''
        user = self.context['user']

        user.set_password(validated_data['password'])
        # if invited user then the account will now be operational.

        user.is_active = True
        user.save()

        # logout user of all devices.
        try:
            Token.objects.get(user=user).delete()
        except Token.DoesNotExist:
            pass

        # update login time, also invalidate current token.
        user.login_now()

        return user

    def update(self, instance, validated_data):
        pass

    class Meta:
        model = User
        fields = ['password']
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }
