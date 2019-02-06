# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator

from rest_framework import response, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from apps.auth import serializers as auth_serializer

from apps.common.permissions import IsNotAuthenticated
from apps.auth.permissions import IsSelfOrCompanyAdmin


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
    serializer_class = auth_serializer.InviteUserSerializer
    queryset = User.objects.all()
    permission_classes = [IsSelfOrCompanyAdmin]

    def update(self, *args, **kwargs):
        '''
        Change serializer for method
        '''
        self.serializer_class = auth_serializer.UpdateUserSerializer
        return super(UserView, self).update(*args, **kwargs)

    @action(detail=False, methods=['post'], authentication_classes=[], permission_classes=[AllowAny])
    def login(self, request):
        serializer = auth_serializer.AuthTokenSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        serializer = auth_serializer.UserSerializer(user)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'])
    def logout(self, request):
        Token.objects.get(user=request.user).delete()
        return response.Response({'res': 'user succesfully loggedout'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='request-reset', authentication_classes=[], permission_classes=[IsNotAuthenticated])
    def request_reset(self, request):
        serializer = auth_serializer.ResetTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
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

    def filter_token(self, token):
        token, user_id = token.split('--')

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise ValidationError({'detail': 'invalid token'})

        if not default_token_generator.check_token(user, token):
            raise ValidationError({'detail': 'invalid token'})

        return (token, user)

    def get(self, request, token):
        try:
            token, _ = self.filter_token(token)
        except ValidationError as e:
            return response.Response(e, status=status.HTTP_404_NOT_FOUND)

        return response.Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, token):
        token, user = self.filter_token(token)
        serilizer = auth_serializer.ResetPasswordSerializer(
            data=request.data, context={
                'request': request,
                'user': user
            }
        )

        serilizer.is_valid(raise_exception=True)
        serilizer.save()

        return response.Response(serilizer.data, status=status.HTTP_200_OK)
