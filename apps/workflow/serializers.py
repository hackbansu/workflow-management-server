# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta

from django.db.transaction import atomic
from django.conf import settings
from django.utils import timezone

from rest_framework import serializers

from apps.common import constant as common_constant
from apps.common.helper import generate_error
from apps.company.models import UserCompany
from apps.company.serializers import UserCompanySerializer
from apps.workflow.helpers import is_time_conflicting, is_task_conflicting, get_parent_start_time
from apps.workflow.models import Workflow, Task, WorkflowAccess
from apps.workflow_template.models import WorkflowTemplate
from apps.workflow_template.serializers import WorkflowTemplateBaseSerializer as WorkflowTemplateBaseSerializer


class TaskBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'workflow', 'title', 'description', 'parent_task',
                  'assignee', 'completed_at', 'start_delta', 'duration', 'status')
        read_only_fields = ('id', 'workflow', 'parent_task', 'completed_at', 'status')


class TaskUpdateSerializer(TaskBaseSerializer):
    class Meta(TaskBaseSerializer.Meta):
        pass

    def validate(self, data):
        '''
        Don't update assignee if user is only assignee and not admin or write accessor
        Check new assignee is of the same company and is an active employee
        Check that user can't update start_delta of the ongoing task
        Check task time conflict
        '''
        employee = self.context['request'].user.active_employee
        instance = self.instance

        isOnlyAssignee = instance.assignee == employee and not employee.is_admin
        isOnlyAssignee = isOnlyAssignee and (not employee.shared_workflows.filter(
            workflow=instance.workflow,
            permission=common_constant.PERMISSION.READ_WRITE
        ).exists())
        if isOnlyAssignee:
            raise serializers.ValidationError(
                generate_error('Assignee does not have permissions to update assignee of the task')
            )

        if instance.status == common_constant.TASK_STATUS.ONGOING and data.get('start_delta'):
            raise serializers.ValidationError(generate_error('start delta could not be updated for ongoing task'))

        if data.get('assignee'):
            if not data['assignee'].company == employee.company:
                raise serializers.ValidationError(generate_error('New assignee must be of the same company'))
            if not data['assignee'].is_active:
                raise serializers.ValidationError(generate_error('Assignee must be an active employee'))

        # check task conflicting if start_delta or duration is updated
        if(data.get('start_delta') or data.get('duration')):
            # calculate expected start time of the task
            task_start_time = data.get('start_delta', instance.start_delta)
            task_parent = instance.parent_task
            if(task_parent):
                task_start_time += get_parent_start_time(task_parent)
            else:
                task_start_time += instance.workflow.start_at
            task_end_time = task_start_time + data.get('duration', instance.duration)
            employee = data.get('assignee', instance.assignee)
            if is_task_conflicting(employee, task_start_time, task_end_time, ignore_tasks_ids=[instance.id]):
                raise serializers.ValidationError(generate_error(
                    'Task time conflict occurred for user {email}'.format(email=employee.user.email)
                ))

        return data

    def update(self, instance, validated_data):
        '''
        override to send mail on task update.
        '''
        instance = super(TaskUpdateSerializer, self).update(instance, validated_data)
        instance.send_mail()

        return instance


class WorkflowAccessBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowAccess
        fields = ('id', 'employee', 'permission')
        read_only_fields = ('id', )


class WorkflowAccessDestroySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowAccess
        fields = ('employee',)
        read_only_fields = ()


class WorkflowAccessCreateSerializer(WorkflowAccessBaseSerializer):
    class Meta(WorkflowAccessBaseSerializer.Meta):
        fields = WorkflowAccessBaseSerializer.Meta.fields + ('workflow',)
        read_only_fields = WorkflowAccessBaseSerializer.Meta.read_only_fields + ('workflow',)

    def validate(self, data):
        '''
        checks that employee belong to the same company as of the user and is active.
        '''
        if not self.context['request'].user.company == data['employee'].company:
            raise serializers.ValidationError(generate_error('Employee must be of the same company'))
        if not data['employee'].is_active:
            raise serializers.ValidationError(generate_error('Employee must be an active employee'))

        return data

    def create(self, validated_data):
        '''
        override to create or update accessor instance.
        '''
        instance, created = WorkflowAccess.objects.get_or_create(
            employee=validated_data['employee'],
            workflow=validated_data['workflow'],
            defaults={'permission': validated_data['permission']}
        )

        if created:
            instance.send_mail()
            return instance

        # employee already have same permission
        if instance.permission == validated_data['permission']:
            return instance

        instance.permission = validated_data['permission']
        instance.save()

        return instance


class WorkflowBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ('id', 'template', 'name', 'creator', 'start_at', 'complete_at',)
        read_only_fields = ('id', 'creator', 'complete_at')

    def validate(self, data):
        '''
        Validate the start date and time is after current date and time.
        '''
        if data['start_at'] < timezone.now():
            raise serializers.ValidationError(generate_error('start date can not be earlier than current time.'))

        return data


class WorkflowCreateSerializer(WorkflowBaseSerializer):
    tasks = TaskBaseSerializer(many=True)
    accessors = WorkflowAccessBaseSerializer(many=True)

    class Meta(WorkflowBaseSerializer.Meta):
        fields = WorkflowBaseSerializer.Meta.fields + ('tasks', 'accessors')

    def validate(self, data):
        '''
        Validates that the assignees and accessors all belong to the same company as of the creator and are all active
        employees. Also validate that tasks of assignees don't conflict with their other tasks.
        '''
        super(WorkflowCreateSerializer, self).validate(data)

        employee = self.context['request'].user.active_employee

        # validate that the assignees belong to the same company as that of the user and are active employees
        tasks = data.get('tasks', [])
        for task in tasks:
            if not task['assignee'].company == employee.company:
                raise serializers.ValidationError(generate_error('Assignees must be of the same company'))
            if not task['assignee'].is_active:
                raise serializers.ValidationError(generate_error('Assignees must be an active employee'))

        # validate that the accessors are of the same company as that of the user and are active employees
        accessors = data.get('accessors', [])
        for accessor in accessors:
            if not accessor['employee'].company == employee.company:
                raise serializers.ValidationError(generate_error('Accessor must be of the same company'))
            if not accessor['employee'].is_active:
                raise serializers.ValidationError(generate_error('Accessor must be an active employee'))

        # validate that every assignee's other tasks don't conflict
        visited_assignees = {}
        prev_task_end_time = data['start_at']
        for task in tasks:
            task_start_time = prev_task_end_time + task['start_delta']
            task_end_time = task_start_time + task['duration']
            employee = task['assignee']
            if is_task_conflicting(employee, task_start_time, task_end_time, visited_assignees):
                raise serializers.ValidationError(generate_error(
                    'Task time conflict occurred for user {email}'.format(email=employee.user.email)
                ))

            prev_task_end_time = task_end_time

        return data

    @atomic
    def create(self, validated_data):
        '''
        override due to nested writes

        Arguments:
            validated_data {dict} -- data recieved after validation
        '''

        tasks = validated_data.pop('tasks', [])
        accessors = validated_data.pop('accessors', [])

        employee = self.context['request'].user.active_employee
        people_assiciated = {}
        people_assiciated[employee.id] = {
            'employee': employee,
            'is_creator': True
        }

        workflow = Workflow.objects.create(creator=employee, **validated_data)

        prev_task = None
        for task in tasks:
            prev_task = Task.objects.create(workflow=workflow, parent_task=prev_task, **task)
            person = people_assiciated.get(prev_task.assignee_id, {})
            if not person:
                person['employee'] = prev_task.assignee
                people_assiciated[prev_task.assignee_id] = person
            if not person.get('task_list'):
                person['task_list'] = []
            person['task_list'].append(prev_task.title)

        for accessor in accessors:
            if accessor.get('employee').id == employee.id:
                # do not add creator in the accessor list.
                continue
            instance = WorkflowAccess.objects.create(workflow=workflow, **accessor)
            person = people_assiciated.get(instance.employee_id, {})
            if not person:
                person['employee'] = instance.employee
                people_assiciated[instance.employee_id] = person
            person['is_shared'] = True
            person['write_permission'] = instance.permission == common_constant.PERMISSION.READ_WRITE

        workflow.send_mail(people_assiciated, is_updated=False)

        return workflow


class WorkflowUpdateSerializer(WorkflowBaseSerializer):
    '''
    Serializer for updating workflow and its tasks. Accessors are not removed via this.
    '''
    class Meta(WorkflowBaseSerializer.Meta):
        read_only_fields = WorkflowBaseSerializer.Meta.read_only_fields + ('template',)

    def update(self, instance, validated_data):
        '''
        override due to sending mails on update
        '''
        instance = super(WorkflowUpdateSerializer, self).update(instance, validated_data)
        instance.send_mail(associated_people_details=None, is_updated=True)
        return instance
