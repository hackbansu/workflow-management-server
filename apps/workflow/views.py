# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from django.utils import timezone

from rest_framework import response, status, viewsets, mixins

from apps.common import constant as common_constant
from apps.company.models import Company, UserCompany
from apps.company.permissions import (
    IsActiveCompanyEmployee,
    IsCompanyAdmin
)
from apps.workflow import serializers as workflow_serializers
from apps.workflow.models import Workflow, Task, WorkflowAccess

User = get_user_model()


class WorkflowView(viewsets.ModelViewSet):
    queryset = Workflow.objects.all()
    permission_classes = (IsActiveCompanyEmployee, IsCompanyAdmin)
    serializer_class = workflow_serializers.WorkflowSerializer

    def get_queryset(self):
        user = self.request.user.active_employee
        employees = Company.objects.filter()
        self.queryset.filter()
