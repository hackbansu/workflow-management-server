# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from django.utils import timezone

from rest_framework import response, status, viewsets, mixins

from apps.common import constant as common_constant
from apps.company import serializers as company_serializer
from apps.company.permissions import (
    IsActiveCompanyEmployee,
    IsCompanyAdmin
)
from apps.workflows.models import Workflow, Task, WorkflowAccess

User = get_user_model()


class WorkflowView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = None
    permission_classes = (IsActiveCompanyEmployee, IsCompanyAdmin)
    # serializer_class =
