# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.db.models import Q

from rest_framework import response, status
from rest_framework.decorators import action, permission_classes
from rest_framework.mixins import (CreateModelMixin, ListModelMixin,
                                   RetrieveModelMixin)
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated

from apps.common import constant as common_constant
from apps.company.models import UserCompany
from apps.company.serializers import UserCompanySerializer, OldUserCompanySerializer, InviteEmployeeSerializer
from apps.auth.serializers import UserSerializer, InviteUserSerializer
from apps.company.permissions import IsInactiveEmployee, IsActiveEmployee, IsCompanyAdmin
from apps.common.permissions import IsNotAuthenticated

User = get_user_model()


class CompanyUserView(CreateModelMixin, GenericViewSet):
    '''
    Company views.
    '''
    queryset = UserCompany.objects.all()
    @permission_classes(permission_classes=[IsNotAuthenticated])
    def create(self, request):
        '''
        create company and user.
        '''
        self.serializer_class = UserCompanySerializer
        self.queryset = UserCompany.objects.all()
        return super(CompanyUserView, self).create(request)

    @action(detail=False, methods=['post'], url_path='new-company', permission_classes=[IsInactiveEmployee])
    def new_company(self, request):
        '''
        create company, only for old users.
        '''
        serializer = OldUserCompanySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[IsActiveEmployee])
    def employees(self, request, pk):
        '''
        list all employees of company.
        '''
        qs = User.objects.filter(
            Q(user_companies__company_id=pk) &
            ~Q(user_companies__status=common_constant.USER_STATUS.INACTIVE)
        )
        serialzer = UserSerializer(qs, many=True)
        return response.Response(serialzer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='invite-employee', permission_classes=[IsCompanyAdmin])
    def invite_employee(self, request):
        '''
        invite employee
        '''
        company = request.user.user_companies.get(
            status=common_constant.USER_STATUS.ACTIVE,
            is_admin=True
        )
        serializer = InviteEmployeeSerializer(
            data=request.data,
            context={
                'request': request,
                'company': company
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data, status=status.HTTP_200_OK)
