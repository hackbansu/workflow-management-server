# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.contrib.auth import get_user_model

from rest_framework import response, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from apps.auth import serializers as auth_serializer
from apps.common import constant as common_constant
from apps.common.helper import filter_reset_password_token

User = get_user_model()

logger = logging.getLogger(__name__)


class UserAuthView(GenericViewSet):
    '''
    login:
        User login with credentials.

    logout:
        Logout current user.

    request_reset:
        Request for password reset.
    '''
    serializer_class = auth_serializer.AuthTokenSerializer
    queryset = User.objects.all()
    authentication_classes = ()

    @action(detail=False, methods=['post'], permission_classes=(AllowAny,))
    def login(self, request):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        serializer = auth_serializer.UserDetailSerializer(instance=user)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'],
            authentication_classes=(TokenAuthentication,),)
    def logout(self, request):
        request.user.auth_token.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], url_path='request-reset', permission_classes=(AllowAny,))
    def request_reset(self, request):
        serializer = auth_serializer.ResetPasswordRequestSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        if serializer.instance is not None:
            serializer.instance.reset_password()

        return response.Response(status=status.HTTP_204_NO_CONTENT)


class ResetPasswordView(RetrieveAPIView, UpdateAPIView):
    '''
    get:
        handle get request for reset token.
    put:
        handle reset password request.
    patch:
        handle reset password request.
    '''
    # Mark: Y both Update.
    serializer_class = auth_serializer.ResetPasswordSerializer
    permission_classes = (AllowAny,)

    def get_object(self):
        _, user = filter_reset_password_token(self.kwargs['token'])
        return user


class ProfileView(RetrieveAPIView, UpdateAPIView):
    '''
    get:
        return login user profile.
    put:
        update login user profile.
    patch:
        partially update login user profile.
    '''
    serializer_class = auth_serializer.UpdateUserSerializer

    def get_object(self):
        return self.request.user
