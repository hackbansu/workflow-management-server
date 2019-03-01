# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model

from rest_framework import serializers

from apps.company.models import UserCompany
from apps.workflow.models import Task, Workflow

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email')
        read_only_fields = ('id', 'first_name', 'last_name', 'email')


class EmployeeBasicSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer()

    class Meta:
        model = UserCompany
        fields = ('id', 'user')
        read_only_fields = ('id', 'user')


class TaskBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'title', 'completed_at')
        read_only_fields = ('id', 'title', 'completed_at')


class WorkflowBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ('id', 'name', 'completed_at')
        read_only_fields = ('id', 'name', 'completed_at')


class IJLEmployeeCountSerializer(serializers.Serializer):
    count = serializers.IntegerField(min_value=0)
    month = serializers.DateTimeField()


class TopEmployeeSerializer(serializers.Serializer):
    employee = EmployeeBasicSerializer()
    avg_task_time = serializers.DurationField()


class WorkflowTimeSerializer(serializers.Serializer):
    workflow = WorkflowBasicSerializer()
    total_time_spent = serializers.DurationField()

    class Meta:
        fields = ('workflow', 'total_time_spent')


class EmployeeReportSerializer(serializers.ModelSerializer):
    time_spent_on_workflows = WorkflowTimeSerializer(many=True)
    number_of_workflows_assigned = serializers.IntegerField(min_value=0)
    number_of_tasks = serializers.IntegerField(min_value=0)
    total_time_spent_on_tasks = serializers.DurationField()
    avg_time_spent_on_tasks = serializers.DurationField()
    max_time_spent_on_tasks = serializers.DurationField()
    min_time_spent_on_tasks = serializers.DurationField()
    total_time_spent_on_workflows = serializers.DurationField()
    avg_time_spent_on_workflows = serializers.DurationField()
    max_time_spent_on_workflows = serializers.DurationField()
    min_time_spent_on_workflows = serializers.DurationField()
    last_task_completed = TaskBasicSerializer()
    last_workflow_completed = WorkflowBasicSerializer()
    workflows_completed_monthly = IJLEmployeeCountSerializer(many=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email',
                  'time_spent_on_workflows',
                  'number_of_workflows_assigned',
                  'number_of_tasks', 'total_time_spent_on_tasks', 'avg_time_spent_on_tasks', 'max_time_spent_on_tasks',
                  'min_time_spent_on_tasks', 'total_time_spent_on_workflows', 'avg_time_spent_on_workflows',
                  'max_time_spent_on_workflows', 'min_time_spent_on_workflows', 'last_task_completed',
                  'last_workflow_completed', 'workflows_completed_monthly')


class assingeeTimeSerializer(serializers.Serializer):
    assignee = EmployeeBasicSerializer()
    time = serializers.DurationField()


class WorkflowReportSerializer(serializers.ModelSerializer):
    unique_assignees = EmployeeBasicSerializer(many=True)
    total_time_spend = serializers.DurationField()
    number_of_assignees = serializers.IntegerField(min_value=0)
    number_of_tasks = serializers.IntegerField(min_value=0)
    average_task_complete_time = serializers.DurationField()
    assingee_with_min_time = assingeeTimeSerializer()
    assingee_with_max_time = assingeeTimeSerializer()
    creator = EmployeeBasicSerializer()

    class Meta:
        model = Workflow
        fields = ('name', 'status', 'start_at', 'completed_at', 'creator', 'unique_assignees', 'total_time_spend',
                  'number_of_assignees', 'number_of_tasks', 'average_task_complete_time', 'assingee_with_min_time',
                  'assingee_with_max_time')
