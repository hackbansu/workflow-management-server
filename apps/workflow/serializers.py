# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
import pytz

from rest_framework import serializers

from apps.common import constant as common_constant
from apps.company.models import UserCompany
from apps.company.serializers import UserCompanySerializer
from apps.workflow.models import Workflow, Task, WorkflowAccess
from apps.workflow_template.models import WorkflowTemplate
from apps.workflow_template.serializers import WorkflowTemplateBaseSerializer as WorkflowTemplateBaseSerializer

utc = pytz.UTC


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
        """
        Don't update assignee if user is only assignee and not admin or write accessor
        Also check new assignee is of the same company
        """
        employee = self.context['request'].user.active_employee
        instance = self.instance

        isOnlyAssignee = instance.assignee == employee and not employee.is_admin
        isOnlyAssignee = isOnlyAssignee and (not employee.shared_workflows.filter(
            workflow=instance.workflow,
            permission=common_constant.PERMISSION.READ_WRITE
        ).exists())
        if isOnlyAssignee:
            raise serializers.ValidationError('Assignee does not have permissions to update assignee of the task.')

        if data.get('assignee', None) and not data['assignee'].company == employee.company:
            raise serializers.ValidationError('New assignee must be of the same company.')

        return data

    def update(self, instance, validated_data):
        instance = super(TaskUpdateSerializer, self).update(instance, validated_data)
        instance.send_mail()

        return instance


class WorkflowAccessBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowAccess
        fields = ('id', 'employee', 'permission')
        read_only_fields = ('id', )


class WorkflowAccessCreateSerializer(WorkflowAccessBaseSerializer):
    class Meta(WorkflowAccessBaseSerializer.Meta):
        fields = WorkflowAccessBaseSerializer.Meta.fields + ('workflow',)
        read_only_fields = WorkflowAccessBaseSerializer.Meta.read_only_fields + ('workflow',)

    def validate(self, data):
        """
        checks that employee and workflow belongs to the same company.
        """
        workflow_id = self.context['request'].parser_context['kwargs']['workflow_id']
        data['workflow'] = Workflow.objects.get(pk=workflow_id)

        if not data['employee'].company == data['workflow'].creator.company:
            raise serializers.ValidationError('Employee must be of the same company')
        return data

    def create(self, validated_data):
        '''
        overrided to send mail after creating new accessor.
        '''
        instance = super(WorkflowAccessCreateSerializer, self).create(validated_data)
        instance.send_mail()
        return instance


class WorkflowAccessUpdateSerializer(WorkflowAccessCreateSerializer):
    class Meta(WorkflowAccessCreateSerializer.Meta):
        read_only_fields = WorkflowAccessCreateSerializer.Meta.read_only_fields + ('employee',)

    def validate(self, data):
        return data

    def update(self, instance, validated_data):
        '''
        override to send mail after update.
        '''
        instance = super(WorkflowAccessUpdateSerializer, self).update(instance, validated_data)
        instance.send_mail()
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
        if data['start_at'].replace(tzinfo=utc) < datetime.now().replace(tzinfo=utc):
            raise serializers.ValidationError('start date can not be earlier than current time.')

        return data


class WorkflowCreateSerializer(WorkflowBaseSerializer):
    tasks = TaskBaseSerializer(many=True)
    accessors = WorkflowAccessBaseSerializer(many=True)

    class Meta(WorkflowBaseSerializer.Meta):
        fields = WorkflowBaseSerializer.Meta.fields + ('tasks', 'accessors')

    def validate(self, data):
        '''
        Validates that the assignees and accessors all belong to the same company as of the creator.
        '''
        super(WorkflowCreateSerializer, self).validate(data)

        employee = self.context['request'].user.active_employee

        # validate that the assignees belong to the same company
        tasks = data.get('tasks', None)
        if tasks:
            for task in tasks:
                if not task['assignee'].company == employee.company:
                    raise serializers.ValidationError('Assignees must be of the same company')

        # validate that the accessors are of the same company
        accessors = data.get('accessors', None)
        if accessors:
            for accessor in accessors:
                if not accessor['employee'].company == employee.company:
                    raise serializers.ValidationError('Accessor must be of the same company')

        return data

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

        if tasks:
            prev_task = None
            for task in tasks:
                prev_task = Task.objects.create(workflow=workflow, parent_task=prev_task, **task)

                person = people_assiciated.get(prev_task.assignee_id, {})
                if not person:
                    person['employee'] = prev_task.assignee
                    people_assiciated[prev_task.assignee_id] = person
                if not person.get('task_list', None):
                    person['task_list'] = []
                person['task_list'].append(prev_task.title)

        if accessors:
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
