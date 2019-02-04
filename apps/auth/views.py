# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator

from rest_framework import response, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_401_UNAUTHORIZED
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from apps.auth.serializers import (AuthTokenSerializer,
                                   ResetPasswordSerializer,
                                   ResetTokenSerializer, UserAuthSerializer)
from apps.common import constant as common_constant
from apps.common.permissions import IsNotAuthenticated
from apps.company.models import UserCompany

User = get_user_model()


class UserView(RetrieveModelMixin, GenericViewSet):
    '''
    User views
    '''
    serializer_class = UserAuthSerializer
    queryset = User.objects.all()

    @action(detail=False, methods=['post'], permission_classes=[IsNotAuthenticated])
    def login(self, request, *args, **kwrds):
        serializer = AuthTokenSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return response.Response({'token': user.token})

    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticated])
    def logout(self, request, *args, **kwrds):
        if request.user.is_authenticated:
            Token.objects.get(user=request.user).delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        return response.Response(status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'], url_path='request-reset', permission_classes=[IsNotAuthenticated])
    def request_reset(self, request):
        serializer = ResetTokenSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        user.reset_password()

        return response.Response(status=status.HTTP_204_NO_CONTENT)


class ResetPasswordView(APIView):
    permission_classes = [IsNotAuthenticated]

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
        print token
        token, user = self.filter_token(token)
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, token):
        token, user = self.filter_token(token)
        serilizer = ResetPasswordSerializer(
            data=request.data,
            context={'request': request, 'user': user}
        )
        serilizer.is_valid(raise_exception=True)
        serilizer.save()

        employee_record = UserCompany.objects.filter(
            user=user,
            status=common_constant.USER_STATUS.INVITED
        )

        if employee_record.exists():
            employee_record.first().status = common_constant.USER_STATUS.ACTIVE
            employee_record.first().save()

        serilizer = UserAuthSerializer(user)
        return response.Response(serilizer.data, status=status.HTTP_200_OK)
