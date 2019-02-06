# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model

from rest_framework import response, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from apps.auth import serializers as auth_serializer
from apps.auth.permissions import IsSelfOrCompanyAdmin
from apps.common.helper import filter_token
from apps.common.permissions import IsNotAuthenticated

User = get_user_model()


class UserView(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    '''
    retreive:
        Retreive user data.

    login:
        User login with credentials.

    logout:
        Logout current user.

    request_reset:
        Request for password reset.
    '''
    serializer_class = auth_serializer.UpdateUserSerializer
    queryset = User.objects.all()
    permission_classes = [IsSelfOrCompanyAdmin]

    @action(detail=False, methods=['post'], authentication_classes=[], permission_classes=[AllowAny])
    def login(self, request):
        serializer = auth_serializer.AuthTokenSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        serializer = auth_serializer.UserSerializer(instance=user)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        request.user.auth_token.delete()
        return response.Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='request-reset', authentication_classes=[], permission_classes=[IsNotAuthenticated])
    def request_reset(self, request):
        serializer = auth_serializer.ResetPasswordRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        User.objects.get(
            email=serializer.validated_data['email']
        ).reset_password()

        return response.Response(status=status.HTTP_204_NO_CONTENT)


class ResetPasswordView(APIView):
    '''
    get:
        handle get request for reset token.
    post:
        handle reset token request.
    '''

    permission_classes = [IsNotAuthenticated]
    authentication_classes = []

    def get(self, request, token):
        try:
            token, _ = filter_token(token)
        except ValidationError as e:
            return response.Response(e, status=status.HTTP_404_NOT_FOUND)

        return response.Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, token):
        token, user = filter_token(token)
        serilizer = auth_serializer.ResetPasswordSerializer(
            data=request.data,
            instance=user,
            context={
                'request': request,
            }
        )

        serilizer.is_valid(raise_exception=True)
        serilizer.save()

        return response.Response(serilizer.data, status=status.HTTP_200_OK)


class InvitationView(APIView):
    '''
    User accept invitaion.
    '''
    permission_classes = [IsNotAuthenticated]
    authentication_classes = []

    def get(self, request, token):
        try:
            token, user = filter_token(token)
        except ValidationError as e:
            return response.Response(e, status=status.HTTP_404_NOT_FOUND)
        user.is_active = True
        user.save()
        return response.Response(status=status.HTTP_204_NO_CONTENT)
