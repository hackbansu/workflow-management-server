# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model

from rest_framework import response, status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin
from rest_framework.viewsets import GenericViewSet

from apps.common import constant as common_constant
from apps.company.models import UserCompany
from apps.company import serializers as company_serializer
from apps.company import permissions as company_permissions
from apps.common.permissions import IsNotAuthenticated

User = get_user_model()


class CompanyUserView(CreateModelMixin, GenericViewSet):
    '''
    create:
        Create User and Company.

    new_company:
        Create new company, only for inactive users.

    employees:
        List all employess of users company.

    invite_employee:
        Invite employee to company.
    '''
    queryset = UserCompany.objects.all()
    serializer_class = company_serializer.UserCompanySignupSerializer
    permission_classes = [IsNotAuthenticated]

    @action(detail=False, methods=['post'], url_path='new-company', permission_classes=[company_permissions.IsInactiveEmployee])
    def new_company(self, request):
        '''
        create company, only for old users.
        '''
        serializer = company_serializer.UserCompanySerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[company_permissions.IsActiveCompanyEmployee])
    def employees(self, request):
        '''
        list all active employees of company.
        '''
        user = request.user

        company = user.user_companies.get(
            status=common_constant.USER_STATUS.ACTIVE
        ).company

        qs = UserCompany.objects.filter(
            company=company,
            status=common_constant.USER_STATUS.ACTIVE
        )
        serialzer = company_serializer.EmployeeSerializer(qs, many=True)

        return response.Response(serialzer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='invite-employee', permission_classes=[company_permissions.IsActiveCompanyAdmin])
    def invite_employee(self, request):
        '''
        invite employee
        '''
        serializer = company_serializer.InviteEmployeeSerializer(
            data=request.data,
            context={
                'request': request
            }
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data, status=status.HTTP_200_OK)
