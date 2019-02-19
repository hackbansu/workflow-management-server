# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from apps.company.serializers import UserCompanySerializer
from apps.workflow.models import Workflow, Task, WorkflowAccess
from apps.workflow_template.models import WorkflowTemplate
from apps.workflow_template.serializers import WorkflowTemplateBaseSerializer as WorkflowTemplateBaseSerializer


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'workflow', 'title', 'description', 'parent_task', 'assignee',
                  'completed_at', 'start_delta', 'status')
        read_only_fields = ('id', 'workflow', 'parent_task', 'completed_at', 'status')


class WorkflowAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowAccess
        fields = ('id', 'employee', 'permission')
        read_only_fields = ('id', )


class WorkflowSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True)
    accessors = WorkflowAccessSerializer(many=True)

    def create(self, validated_data):
        '''
        override due to nested writes

        Arguments:
            validated_data {dict} -- data recieved after validation
        '''

        tasks = validated_data.pop('tasks')
        accessors = validated_data.pop('accessors')
        employee = self.context['request'].user.active_employee
        workflow = Workflow.objects.create(creator=employee, **validated_data)
        workflow.send_mail(is_updated=False)

        if tasks:
            prev_task = None
            for task in tasks:
                prev_task = Task.objects.create(
                    workflow=workflow, parent_task=prev_task, **task)
                prev_task.send_mail(is_new=True)

        if accessors:
            for accessor in accessors:
                instance = WorkflowAccess.objects.create(
                    workflow=workflow, **accessor)
                instance.send_mail(is_updated=False)

        return workflow

    def update(self, instance, validated_data):
        pass

    class Meta:
        model = Workflow
        fields = ('id', 'template', 'name', 'creator', 'start_at',
                  'complete_at', 'duration', 'tasks', 'accessors')
        read_only_fields = ('id', 'creator', 'complete_at')
