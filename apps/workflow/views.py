# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

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
from apps.workflow.tasks import start_task

User = get_user_model()
UPDATE_METHODS = ('PATCH', 'PUT')

logger = logging.getLogger(__name__)


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
            methods=['post'],
            url_path='accessor',
            serializer_class=workflow_serializers.WorkflowAccessCreateSerializer)
    def create_update_accessor(self, request, *args, **kwargs):
        '''
        workflow's accessor create or update
        '''
        workflow_instance = self.get_object()
        serializer = self.get_serializer(data=request.data, )
        serializer.is_valid(raise_exception=True)
        serializer.save(workflow=workflow_instance)

        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True,
            methods=['delete'],
            url_path='accessor/delete',
            serializer_class=workflow_serializers.WorkflowAccessDestroySerializer)
    def delete_accessor(self, request, *args, **kwargs):
        '''
        workflow's accessor delete
        '''
        workflow_instance = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data

        instance = get_object_or_404(WorkflowAccess.objects.all(),
                                     employee=data['employee'],
                                     workflow=workflow_instance)

        instance.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)


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

    @action(detail=True, methods=['patch'], url_path='completed')
    def mark_task_completion(self, request, *args, **kwargs):
        '''
        Mark task as completed and intiate next task after its start delta
        '''
        task_instance = self.get_object()
        # bad request if task is not ongoing.
        if(not task_instance.status == common_constant.TASK_STATUS.ONGOING):
            return response.Response(status=status.HTTP_400_BAD_REQUEST)

        task_instance.status = common_constant.TASK_STATUS.COMPLETE
        task_instance.completed_at = timezone.now()
        task_instance.save()

        # get the next task
        next_task = Task.objects.filter(parent_task=task_instance)

        if next_task.exists():
            # call celery task to initiate next task after it's start delta
            next_task = next_task[0]
            start_task.apply_async((next_task), eta=task_instance.completed_at + next_task.start_delta)
        else:
            # mark workflow as completed
            task_instance.workflow.completed_at = timezone.now()
            logger.info('Workflow %s is now complete' % (task_instance.workflow.name))

        return response.Response(status=status.HTTP_200_OK)
