# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model

from rest_framework import serializers

from apps.company.serializers import UserCompanySignupSerializer
from apps.workflow.models import Workflow
from apps.workflow.serializers import TaskBaseSerializer, WorkflowBaseSerializer

User = get_user_model()


class IJLEmployeeCountSerializer(serializers.Serializer):
    count = serializers.IntegerField(min_value=0)
    month = serializers.DateTimeField()


class TopEmployeeSerializer(serializers.Serializer):
    employee = UserCompanySignupSerializer()
    avg_task_time = serializers.DurationField()


class WorkflowTimeSerializer(serializers.Serializer):
    workflow = WorkflowBaseSerializer()
    total_time_spent = serializers.DurationField()

    class Meta:
        fields = ('workflow', 'total_time_spent')


class EmployeeReportSerializer(serializers.ModelSerializer):
    time_spent_on_workflows = WorkflowTimeSerializer(many=True)
    number_of_workflows_assigned = serializers.IntegerField(min_value=0)
    number_of_tasks = serializers.IntegerField(min_value=0)
    total_time_spent_on_tasks = serializers.DurationField()
    Avg_time_spent_on_tasks = serializers.DurationField()
    max_time_spent_on_tasks = serializers.DurationField()
    min_time_spent_on_tasks = serializers.DurationField()
    total_time_spent_on_workflows = serializers.DurationField()
    avg_time_spent_on_workflows = serializers.DurationField()
    max_time_spent_on_workflows = serializers.DurationField()
    min_time_spent_on_workflows = serializers.DurationField()
    last_task_completed = TaskBaseSerializer()
    last_workflow_completed = WorkflowBaseSerializer()
    workflows_completed_monthly = IJLEmployeeCountSerializer(many=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email',
                  'time_spent_on_workflows',
                  'number_of_workflows_assigned',
                  'number_of_tasks', 'total_time_spent_on_tasks', 'Avg_time_spent_on_tasks', 'max_time_spent_on_tasks',
                  'min_time_spent_on_tasks', 'total_time_spent_on_workflows', 'avg_time_spent_on_workflows',
                  'max_time_spent_on_workflows', 'min_time_spent_on_workflows', 'last_task_completed',
                  'last_workflow_completed', 'workflows_completed_monthly')


class WorkflowReportSerializer(serializers.ModelSerializer):
    unique_assignees = UserCompanySignupSerializer(many=True)
    total_time_spend = serializers.DurationField()
    number_of_assignees = serializers.IntegerField(min_value=0)
    number_of_tasks = serializers.IntegerField(min_value=0)
    average_task_complete_time = serializers.DurationField()
    assingee_with_min_time = UserCompanySignupSerializer()
    assingee_with_max_time = UserCompanySignupSerializer()

    class Meta:
        model = Workflow
        fields = ('name', 'status', 'start_at', 'completed_at', 'creator', 'unique_assignees', 'total_time_spend',
                  'number_of_assignees', 'number_of_tasks', 'average_task_complete_time', 'assingee_with_min_time',
                  'assingee_with_max_time')
