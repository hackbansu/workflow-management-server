# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db.transaction import atomic
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from rest_framework import response, status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import (
    CreateModelMixin, ListModelMixin, RetrieveModelMixin,
    UpdateModelMixin, DestroyModelMixin
)
from rest_framework.viewsets import GenericViewSet

from apps.common import constant as common_constant
from apps.company.models import Company, UserCompany
from apps.company.permissions import (IsActiveCompanyEmployee, IsCompanyAdmin)
from apps.workflow import permissions as workflow_permissions
from apps.workflow import serializers as workflow_serializers
from apps.workflow.models import Workflow, Task, WorkflowAccess
from apps.workflow.tasks import start_task
from apps.history.models import History
from apps.history.serializers import HistorySerializer

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
            methods=['get'],
            url_path='accessor/all',
            serializer_class=workflow_serializers.WorkflowAccessBaseSerializer)
    def list_accessors(self, request, *args, **kwargs):
        '''
            list all accessors of workflow.
        '''

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
        serializer = self.get_serializer(
            data=request.data,
            instance=workflow_instance,
            context=context
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # retreive all permissions.
        serializer = workflow_serializers.WorkflowAccessBaseSerializer(
            instance=workflow_instance.accessors.all(),
            many=True
        )

        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True,
            methods=['get'],
            serializer_class=HistorySerializer)
    def history(self, request, pk):
        workflow_instance = self.get_object()
        tasks_qs = Task.objects.filter(workflow=workflow_instance)
        permission_qs = WorkflowAccess.objects_all.filter(
            workflow=workflow_instance)
        history = History.objects.exclude(field_name='id').filter(
            Q(workflows=workflow_instance) |
            Q(workflow_accesses__in=permission_qs, field_name='permission') |
            Q(tasks__in=tasks_qs)
        )
        serializer = self.get_serializer(instance=history, many=True)
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

    @action(detail=True, methods=['patch'], url_path='completed')
    @atomic
    def mark_task_completion(self, request, *args, **kwargs):
        '''
        Mark task as completed and intiate next task after its start delta if it's start delta is higher than celery
        scheduled task schedule.
        '''
        task_instance = self.get_object()
        # bad request if task is not ongoing.
        if(not task_instance.status == common_constant.TASK_STATUS.ONGOING):
            return response.Response(status=status.HTTP_400_BAD_REQUEST)

        task_instance.status = common_constant.TASK_STATUS.COMPLETE
        task_instance.completed_at = timezone.now()
        task_instance.save()

        next_task = Task.objects.filter(parent_task=task_instance)

        if next_task.exists():
            # send start task to celery if start delta of next task is less than celery scheduled task schedule
            next_task = next_task[0]
            if next_task.start_delta < timedelta(seconds=common_constant.TASK_PERIODIC_TASK_SCHEDULE_SECONDS):
                next_task.status = common_constant.TASK_STATUS.SCHEDULED
                next_task.save()
                start_task.apply_async(
                    (next_task.id,), countdown=next_task.start_delta.seconds)
        else:
            # mark workflow as completed
            task_instance.workflow.status = common_constant.WORKFLOW_STATUS.COMPLETE
            task_instance.workflow.completed_at = timezone.now()
            task_instance.workflow.save()
            logger.info('Workflow %s is now complete' %
                        (task_instance.workflow.name))

        return response.Response(status=status.HTTP_200_OK)

    @action(detail=True,
            methods=['get'],
            serializer_class=HistorySerializer)
    def history(self, request, pk):
        task_instance = self.get_object()
        history = History.objects.exclude(field_name='id').filter(
            tasks=task_instance
        )
        serializer = self.get_serializer(instance=history, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)
