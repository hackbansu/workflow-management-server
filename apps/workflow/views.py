# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from django_filters import rest_framework as filters

from rest_framework import response, status, viewsets, mixins
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from apps.common import constant as common_constant
from apps.company.models import Company, UserCompany
from apps.company.permissions import (
    IsActiveCompanyEmployee,
    IsCompanyAdmin
)
from apps.workflow import serializers as workflow_serializers
from apps.workflow.models import Workflow, Task, WorkflowAccess
from apps.workflow.permissions import WorkflowAccessPermission as WorkflowAccessPermission

User = get_user_model()


class WorkflowCRULView(CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    queryset = Workflow.objects.all()
    permission_classes = (WorkflowAccessPermission,)
    serializer_class = workflow_serializers.WorkflowSerializer

    def update(self, request, *args, **kwargs):
        self.serializer_class = workflow_serializers.WorkflowUpdateSerializer
        return super(WorkflowCRLView, self).update(request, *args, **kwargs)
    
    def get_queryset(self):
        employee = self.request.user.active_employee

        if(employee.is_admin):
            return self.queryset.filter(creator__company=employee.company)

        return self.queryset.filter(Q(tasks__assignee=employee) | Q(accessors__employee=employee)).distinct()


class TaskULView(UpdateModelMixin, ListModelMixin, GenericViewSet):
    queryset = Task.objects.all()
    permission_classes = ()

    def get_queryset(self):
        employee = self.request.user.active_employee

        if(employee.is_admin):
            return self.queryset.filter(creator__company=employee.company)

        return self.queryset.filter(Q(tasks__assignee=employee) | Q(accessors__employee=employee)).distinct()