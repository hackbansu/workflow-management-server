# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from rest_framework import response, status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import (CreateModelMixin, ListModelMixin, RetrieveModelMixin,
                                   UpdateModelMixin, DestroyModelMixin)
from rest_framework.viewsets import GenericViewSet

from apps.common import constant as common_constant
from apps.company.models import Company, UserCompany
from apps.company.permissions import (IsActiveCompanyEmployee, IsCompanyAdmin)
from apps.workflow import permissions as workflow_permissions
from apps.workflow import serializers as workflow_serializers
from apps.workflow.models import Workflow, Task, WorkflowAccess

User = get_user_model()
UPDATE_METHODS = ('PATCH', 'PUT')


class WorkflowCRULView(CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    queryset = Workflow.objects.all()
    permission_classes = (workflow_permissions.WorkflowAccessPermission,)
    serializer_class = workflow_serializers.WorkflowCreateSerializer

    def get_serializer_class(self):
        if self.request.method in UPDATE_METHODS:
            return workflow_serializers.WorkflowUpdateSerializer
        return self.serializer_class

    def get_queryset(self):
        employee = self.request.user.active_employee

        if(employee.is_admin):
            return self.queryset.filter(creator__company=employee.company)

        return self.queryset.filter(Q(tasks__assignee=employee) | Q(accessors__employee=employee)).distinct()

    @action(detail=True,
            methods=['get'],
            url_path='accessor/all',
            serializer_class=workflow_serializers.WorkflowAccessBaseSerializer)
    def list_accessors(self, request, *args, **kwargs):
        workflow_instance = self.get_object()
        serilizer = self.get_serializer(
            instance=workflow_instance.accessors.all(), many=True)
        return response.Response(serilizer.data, status=status.HTTP_200_OK)

    @action(detail=True,
            methods=['post'],
            url_path='accessor',
            serializer_class=workflow_serializers.WorkflowAccessUpdateSerializer)
    def create_update_accessor(self, request, *args, **kwargs):
        '''
        workflow's accessor create or update
        '''
        workflow_instance = self.get_object()

        # update context for workflow instance.
        context = self.get_serializer_context()
        context['workflow'] = workflow_instance

        # permission operations.
        serializer = self.get_serializer(data=request.data, instance=workflow_instance, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # retreive all permissions.
        serializer = workflow_serializers.WorkflowAccessBaseSerializer(
            instance=workflow_instance.accessors.all(),
            many=True
        )

        return response.Response(serializer.data, status=status.HTTP_200_OK)


class TaskULView(RetrieveModelMixin, UpdateModelMixin, ListModelMixin, GenericViewSet):
    queryset = Task.objects.all()
    permission_classes = (workflow_permissions.TaskAccessPermission,)
    serializer_class = workflow_serializers.TaskUpdateSerializer

    def get_queryset(self):
        employee = self.request.user.active_employee

        # admin can see all tasks of the company
        if(employee.is_admin):
            return self.queryset.filter(workflow__creator__company=employee.company)

        return self.queryset.filter(Q(assignee=employee) | Q(workflow__accessors__employee=employee)).distinct()
