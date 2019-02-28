# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from itertools import chain
import logging
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.db.models import ExpressionWrapper, F, Count, Sum, Avg, Max, Min, DurationField
from django.db.models import functions as db_functions
from django.utils import timezone

from rest_framework import generics, mixins, response, status, views, viewsets
from rest_framework.response import Response

from apps.common import constant as common_constant
from apps.company.models import UserCompany
from apps.workflow.models import Workflow, Task
from apps.report.permissions import IsCompanyAdmin
from apps.report.serializers import IJLEmployeeCountSerializer, EmployeeReportSerializer, WorkflowReportSerializer

User = get_user_model()

DIFF_EXPR_NO_PARENT = ExpressionWrapper(
    F('completed_at') - F('workflow__start_at') - F('start_delta'),
    output_field=DurationField()
)
DIFF_EXPR_HAS_PARENT = ExpressionWrapper(
    F('completed_at') - F('parent_task__completed_at') - F('start_delta'),
    output_field=DurationField()
)


class IJLEmployeeCount(generics.GenericAPIView):
    queryset = UserCompany.objects.all()
    serializer_class = IJLEmployeeCountSerializer
    permission_classes = (IsCompanyAdmin,)

    def get_queryset(self):
        company = self.request.user.company
        return self.queryset.filter(company=company)

    def get_monthly_count_data(self, employees):
        data = employees.annotate(
            month=db_functions.TruncMonth('join_at')
        ).values('month').annotate(count=Count('id')).values('count', 'month')
        return self.get_serializer(data, many=True).data

    def get(self, request, format=None):
        '''
        Returns number of users invited, joined and left company within 12 months (month wise)
        '''
        employees = self.get_queryset()
        past_12_months = timezone.now() - timedelta(days=365)
        response_data = {}

        # users who were invited to the company
        response_data['invited_users'] = self.get_monthly_count_data(employees.filter(created__gt=past_12_months))
        # users who joined the company
        response_data['joined_users'] = self.get_monthly_count_data(employees.filter(join_at__gt=past_12_months))
        # users who left the company
        response_data['left_users'] = self.get_monthly_count_data(employees.filter(left_at__gt=past_12_months))

        return Response(response_data, status=status.HTTP_200_OK)


class EmployeeReport(generics.RetrieveAPIView):
    queryset = UserCompany.objects.all()
    permission_classes = (IsCompanyAdmin,)
    serializer_class = EmployeeReportSerializer

    def insert_workflow(self, objs):
        workflow_ids = [instance['workflow'] for instance in objs]
        workflows = Workflow.objects.filter(id__in=workflow_ids).order_by('id')

        for idx, instance in enumerate(objs):
            instance['workflow'] = workflows[idx]

    def retrieve(self, request, *args, **kwargs):
        '''
        override to serializer more user data
        '''
        employee = self.get_object()
        past_12_months = timezone.now() - timedelta(days=365)

        tasks_associated = Task.objects.filter(assignee=employee)
        tasks_time = calculate_completed_tasks_time_spent(tasks_associated)

        workflows_associated = Workflow.objects.filter(tasks__assignee=employee).distinct()
        workflows_time = tasks_time.values('workflow', 'time_spent').annotate(
            total_time_spent=Sum('time_spent')
        ).values('workflow', 'total_time_spent')

        self.insert_workflow(workflows_time)

        data = {
            'first_name': employee.user.first_name,
            'last_name': employee.user.last_name,
            'email': employee.user.email,
            'time_spent_on_workflows': workflows_time
        }

        data['number_of_workflows_assigned'] = workflows_associated.count()
        data['number_of_tasks'] = tasks_associated.count()
        data['total_time_spent_on_tasks'] = tasks_time.aggregate(total_time=Sum('time_spent'))['total_time']
        data['Avg_time_spent_on_tasks'] = tasks_time.aggregate(avg_time=Avg('time_spent'))['avg_time']
        data['min_time_spent_on_tasks'] = tasks_time.aggregate(min_time=Min('time_spent'))['min_time']
        data['max_time_spent_on_tasks'] = tasks_time.aggregate(max_time=Max('time_spent'))['max_time']
        data['total_time_spent_on_workflows'] = workflows_time.aggregate(
            total_time=Sum('total_time_spent')
        )['total_time']
        data['avg_time_spent_on_workflows'] = workflows_time.aggregate(avg_time=Avg('total_time_spent'))['avg_time']
        data['max_time_spent_on_workflows'] = workflows_time.aggregate(max_time=Max('total_time_spent'))['max_time']
        data['min_time_spent_on_workflows'] = workflows_time.aggregate(min_time=Min('total_time_spent'))['min_time']
        data['last_task_completed'] = tasks_associated.order_by('-completed_at').first()
        data['last_workflow_completed'] = workflows_associated.order_by('-completed_at').first()

        data['workflows_completed_monthly'] = workflows_associated.filter(
            status=common_constant.WORKFLOW_STATUS.COMPLETE,
            completed_at__gt=past_12_months
        ).annotate(
            month=db_functions.TruncMonth('completed_at')
        ).values('month').annotate(count=Count('id')).values('count', 'month')

        serializer = self.get_serializer(data)
        return Response(serializer.data)


def calculate_completed_tasks_time_spent(tasks):
    first_tasks_completed = tasks.filter(
        parent_task__isnull=True,
        status=common_constant.TASK_STATUS.COMPLETE
    )
    other_tasks_completed = tasks.filter(
        parent_task__isnull=False,
        status=common_constant.TASK_STATUS.COMPLETE
    )

    first_tasks_time = first_tasks_completed.annotate(time_spent=DIFF_EXPR_NO_PARENT)
    other_tasks_time = other_tasks_completed.annotate(time_spent=DIFF_EXPR_HAS_PARENT)

    return first_tasks_time.union(other_tasks_time)


class WorkflowReport(generics.RetrieveAPIView):
    queryset = Workflow.objects.all()
    permission_classes = (IsCompanyAdmin,)
    serializer_class = WorkflowReportSerializer

    def retrieve(self, request, *args, **kwargs):
        '''
        override to serializer more workflow data
        '''
        workflow = self.get_object()
        tasks_time = calculate_completed_tasks_time_spent(workflow.tasks)

        data = {
            'name': workflow.name,
            'status': workflow.status,
            'start_at': workflow.start_at,
            'completed_at': workflow.completed_at,
            'creator': workflow.creator,
        }

        data['unique_assignees'] = UserCompany.objects.filter(tasks__workflow=workflow).distinct()
        data['total_time_spend'] = (
            workflow.completed_at if workflow.completed_at else timezone.now()
        ) - workflow.start_at
        data['number_of_assignees'] = data['unique_assignees'].count()
        data['number_of_tasks'] = workflow.tasks.count()
        data['average_task_complete_time'] = tasks_time.aggregate(Avg('time_spent'))['time_spent__avg']
        data['assingee_with_min_time'] = tasks_time.earliest('time_spent').assignee
        data['assingee_with_max_time'] = tasks_time.latest('time_spent').assignee

        serializer = self.get_serializer(data)
        return Response(serializer.data)
