# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

from django.contrib.auth import get_user_model

from rest_framework import response, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.generics import GenericAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.authentication import TokenAuthentication

from apps.auth import serializers as auth_serializer
from apps.common.helper import filter_reset_password_token, filter_invite_token
from apps.common.permissions import IsNotAuthenticated
from apps.common import constant as common_constant

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
    authentication_classes = []

    @action(detail=False, methods=['post'],)
    def login(self, request):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        serializer = auth_serializer.UserDetailSerializer(instance=user)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], authentication_classes=[TokenAuthentication],  permission_classes=[IsAuthenticated])
    def logout(self, request):
        request.user.auth_token.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], url_path='request-reset',)
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
    serializer_class = auth_serializer.ResetPasswordSerializer

    def get_object(self):
        _, user = filter_reset_password_token(self.kwargs['token'])
        return user


class InvitationView(GenericAPIView):
    '''
    get:
        handle get request for invitation token.
    put:
        handle reset invitation request.
    patch:
        handle reset invitation request.
    '''
    serializer_class = auth_serializer.InvitationSerializer

    def get_object(self):
        _, user, user_company = filter_invite_token(self.kwargs['token'])
        return (user, user_company)

    def get(self, request, token):
        user, user_company = filter_invite_token(token)
        if user.is_active:
            user_company.status = common_constant.USER_STATUS.ACTIVE
            user_company.save()

            # delete other invitaions, if have any
            qs = user.user_companies.filter(
                status=common_constant.USER_STATUS.INVITED
            )
            if qs.exists():
                qs.delete()

            return response.Response(status=status.HTTP_204_NO_CONTENT)
        return response.Response(status=status.HTTP_200_OK)

    def put(self, request, token):
        return self.patch(request, token)

    def patch(self, request, token):
        user, user_company = filter_invite_token(token)
        serilizer = self.get_serializer(
            data=request.data,
            instance=user,
            context={
                'request': request,
                'user_company': user_company
            }
        )

        serilizer.is_valid(raise_exception=True)
        serilizer.save()
        return response.Response(serilizer.data, status=status.HTTP_200_OK)


class ProfileView(RetrieveAPIView, UpdateAPIView):
    '''
    get:
        return login user profile.
    put:
        update login user profile.
    patch:
        partially update login user profile.
    '''
    permission_classes = [IsAuthenticated]
    serializer_class = auth_serializer.UpdateUserSerializer

    def get_object(self):
        return self.request.user
