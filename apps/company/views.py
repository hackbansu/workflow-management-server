# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from django.utils import timezone

from rest_framework import response, status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin, DestroyModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

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

from apps.common.helper import filter_invite_token
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
    permission_classes = (IsCompanyAdmin,)
    serializer_class = company_serializer.CompanySerializer


class CreateCompanyUserView(CreateModelMixin, CompanyBaseClassView):
    '''
    create:
        Create User and Company.
    '''
    serializer_class = company_serializer.UserCompanySignupSerializer
    authentication_classes = []
    permission_classes = (AllowAny,)


class CreateCompanyView(CompanyBaseClassView):
    '''
    new_company:
        Create company for old user
    '''
    serializer_class = company_serializer.UserCompanySerializer
    permission_classes = (IsInactiveEmployee,)

    @action(detail=False, methods=['post'], url_path='new-company',)
    def new_company(self, request):
        '''
        create company, only for old users.
        '''
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class EmployeeCompanyView(ListModelMixin, UpdateModelMixin, DestroyModelMixin, CompanyBaseClassView):
    '''
    my_company:
        Return company of employee
    partial_update:
        update employee details.
    destroy:
        make user inactive in active company
    '''
    serializer_class = company_serializer.EmployeeAdminSerializer
    permission_classes = (
        company_permissions.IsActiveCompanyEmployee,
        company_permissions.IsActiveCompanyAdmin,
    )
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('status', 'is_admin')

    def get_queryset(self):
        return self.queryset.filter(
            company=self.request.user.company
        )

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
        instance = self.get_queryset().get(
            user=request.user,
            company=request.user.company,
            status=common_constant.USER_STATUS.ACTIVE
        )
        serializer = company_serializer.EmployeeCompanySerializer(
            instance=instance
        )
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class RetreiveEmployee(RetrieveModelMixin, EmployeeCompanyView):
    permission_classes = (IsActiveCompanyEmployee,)


class EmployeesView(ListModelMixin, GenericViewSet):
    '''
    employees:
        return employees of company, can be filtered on the basis of status and admin is possible.
    '''

    serializer_class = company_serializer.EmployeesSerializer
    permission_classes = (company_permissions.IsActiveCompanyEmployee,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('status', 'is_admin')
    queryset = UserCompany.objects.all()

    def get_queryset(self):
        employee = self.request.user.active_employee
        qs = self.queryset.filter(
            company=employee.company,
            status=common_constant.USER_STATUS.ACTIVE
        )
        return qs


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


class InvitationView(GenericAPIView):
    '''
    get:
        handle get request for invitation token.
    put:
        handle invitation request to activate user, if required reset password.
    patch:
        handle invitation request to activate user, if required reset password.
    '''
    serializer_class = company_serializer.InvitationSerializer
    permission_classes = (AllowAny,)

    def get_serializer_context(self,):
        """
        overrided to provide user_company instance to the serializer.
        """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self,
            'user_company': self.user_company
        }

    def get_object(self):
        _, user, user_company = filter_invite_token(self.kwargs['token'])
        return (user, user_company)

    def get(self, request, token):
        user, user_company = self.get_object()
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
        user, user_company = self.get_object()
        self.user_company = user_company
        serilizer = self.get_serializer(
            data=request.data,
            instance=user,
        )

        serilizer.is_valid(raise_exception=True)
        serilizer.save()
        return response.Response(serilizer.data, status=status.HTTP_200_OK)
