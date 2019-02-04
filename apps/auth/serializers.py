from __future__ import unicode_literals

from new import instance

from django.contrib.auth import get_user_model
from django.contrib.syndication.views import FeedDoesNotExist

from rest_framework import serializers
from rest_framework.compat import authenticate
from rest_framework.authtoken.models import Token

from apps.common import constant as common_constant
from apps.company.models import UserCompany

User = get_user_model()


class InviteUserSerializer(serializers.ModelSerializer):
    def validate_email(self, value):
        qs = User.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError(
                {'detail': 'This email is already taken'})
        return value

    class Meta:
        model = User
        fields = [
            'email', 'first_name',
            'last_name'
        ]
        extra_kwargs = {
            'email': {
                'help_text': 'email field, need to be unique, will be trated as username, required'
            },
            'first_name': {
                'help_text': 'user first name'
            },
            'last_name': {
                'help_text': 'user last name'
            },
        }


class UserSerializer(InviteUserSerializer):
    '''
    auth.user model serializer.
    '''

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        instance = super(UserSerializer, self).update(instance, validated_data)

        if validated_data.get('password', None):
            instance.set_password(validated_data.get('password'))

        instance.save()
        return instance

    class Meta(InviteUserSerializer.Meta):
        fields = InviteUserSerializer.Meta.fields
        extra_kwargs = InviteUserSerializer.Meta.extra_kwargs
        fields += [
            'password', 'profile_photo'
        ]
        extra_kwargs.update({
            'password': {
                'write_only': True,
                'help_text': 'password for the account, required'
            },
            'profile_photo': {
                'help_text': 'user profile photo '
            }
        })


class UserAuthSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields
        extra_kwargs = UserSerializer.Meta.extra_kwargs
        fields += [
            'id', 'token'
        ]
        extra_kwargs.update({
            'id': {
                'read_only': True,
                'help_text': 'unique user id'
            },
            'token': {
                'help_text': 'user authentication token',
                'read_only': True
            }
        })


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                username=email, password=password)
            # The authenticate call simply returns None for is_active=False
            # users.
            if not user:
                msg = 'Unable to log in with provided credentials.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Must include "email" and "password".'
            raise serializers.ValidationError(msg, code='authorization')
        
        user.login_now()
        
        attrs['user'] = user
        return attrs


class ResetTokenSerializer(AuthTokenSerializer):
    password = None

    def validate(self, attrs):
        email = attrs.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                attrs['user'] = user
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {'detail': 'email not registered'})
        return attrs


class ResetPasswordSerializer(AuthTokenSerializer):
    email = None

    def validate(self, attr):
        return attr

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = self.context.get('user', None)

        user.set_password(password)
        # if invited user then the account will now be operational.

        user.is_active = True
        user.save()

        # logout user of all devices.
        try:
            Token.objects.get(user=user).delete()
        except Token.DoesNotExist:
            pass

        # login user with new credentials, also invalidate current token.
        user.login_now()

        return user
