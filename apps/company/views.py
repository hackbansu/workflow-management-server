# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from django.utils import timezone

from rest_framework import response, status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.viewsets import GenericViewSet

from apps.common import constant as common_constant
from apps.company import permissions as company_permissions
from apps.company import serializers as company_serializer
from apps.company.models import UserCompany, Company
from apps.company.permissions import (
    IsActiveCompanyAdmin,
    IsActiveCompanyEmployee,
    IsInactiveEmployee,
    IsCompanyAdmin
)
from apps.company.tasks import invite_via_csv


User = get_user_model()


class CompanyBaseClassView(GenericViewSet):
    '''
    Base class for company views.
    '''
    queryset = UserCompany.objects.all()


class UpdateCompanyView(UpdateModelMixin, GenericViewSet):
    '''
    Update Company details.
    '''
    queryset = Company.objects.all()
    permission_classes = [IsCompanyAdmin]
    serializer_class = company_serializer.CompanySerializer


class CreateCompanyUserView(CreateModelMixin, CompanyBaseClassView):
    '''
    create:
        Create User and Company.
    '''
    serializer_class = company_serializer.UserCompanySignupSerializer
    authentication_classes = []


class CreateCompanyView(CompanyBaseClassView):
    '''
    new_company:
        Create company for old user
    '''
    serializer_class = company_serializer.UserCompanySerializer
    permission_classes = [IsInactiveEmployee]

    @action(detail=False, methods=['post'], url_path='new-company',)
    def new_company(self, request):
        '''
        create company, only for old users.
        '''
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class EmployeeCompanyView(UpdateModelMixin, DestroyModelMixin, CompanyBaseClassView):
    '''
    my_company:
        Return company of employee
    partial_update:
        update employee details.
    destroy:
        make user inactive in active company
    '''
    serializer_class = company_serializer.EmployeeSerializer
    permission_classes = (IsActiveCompanyAdmin,)

    def perform_destroy(self, instance):
        if instance.status == common_constant.USER_STATUS.INVITED:
            instance.delete()
        elif instance.status == common_constant.USER_STATUS.ACTIVE:
            instance.status = common_constant.USER_STATUS.INACTIVE
            instance.left_at = timezone.now()
            instance.save()

    @action(detail=False, url_path='my-company', permission_classes=[IsActiveCompanyEmployee])
    def my_company(self, request):
        '''
        employee's company detail
        '''
        instance = self.get_queryset().get(user=request.user, company=request.user.company)
        serializer = company_serializer.EmployeeCompanySerializer(
            instance=instance
        )
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class EmployeesView(GenericViewSet):
    '''
    employees:
        return employees of company, can be filtered on the basis of status and admin is possible.
    '''

    serializer_class = company_serializer.EmployeeSerializer
    permission_classes = [company_permissions.IsActiveCompanyEmployee]
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('status', 'is_admin')
    queryset = UserCompany.objects.all()

    def get_queryset(self):
        return self.queryset.filter(
            company=self.request.user.company,
        )

    @action(detail=False, methods=['get'], )
    def employees(self, request):
        '''
        list all employees of company.
        '''
        queryset = self.filter_queryset(self.get_queryset())
        serialzer = self.get_serializer(queryset, many=True)

        return response.Response(serialzer.data, status=status.HTTP_200_OK)


class InviteEmployeeView(GenericViewSet):
    '''
    Invite User to the company with this view.
    '''
    serializer_class = company_serializer.InviteEmployeeSerializer
    permission_classes = (company_permissions.IsActiveCompanyEmployee,
                          company_permissions.IsCompanyAdmin)
    queryset = UserCompany.objects.all()

    @action(detail=False, methods=['post'], url_path='invite-employee',)
    def invite_employee(self, request):
        '''
        invite employee
        '''
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='invite-employee-csv',)
    def invite_employee_csv(self, request):
        '''
        parse employees data from csv file and invite them
        '''
        serializer = company_serializer.UserCompanyCsvSerializer(
            data=request.data,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        invite_via_csv.delay(instance.id)

        return response.Response(serializer.data, status=status.HTTP_200_OK)
