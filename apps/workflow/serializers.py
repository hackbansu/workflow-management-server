# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

from datetime import timedelta
from django.db.transaction import atomic
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from django_bulk_update.helper import bulk_update

from rest_framework import serializers

from apps.common import constant as common_constant
from apps.common.helper import generate_error
from apps.company.models import UserCompany
from apps.company.serializers import UserCompanySerializer
from apps.workflow.helpers import is_time_conflicting, is_task_conflicting, get_parent_start_time
from apps.workflow.models import Workflow, Task, WorkflowAccess
from apps.workflow.tasks import start_workflow, send_permission_mail
from apps.workflow_template.models import WorkflowTemplate
from apps.workflow_template.serializers import WorkflowTemplateBaseSerializer as WorkflowTemplateBaseSerializer
from apps.history.helpers import update_bulk_history, delete_bulk_history, create_bulk_history

logger = logging.getLogger(__name__)


class FilteredWorkflowAccessListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        data = data.filter(is_active=True)
        return super(FilteredWorkflowAccessListSerializer, self).to_representation(self, data)


class TaskBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'workflow', 'title', 'description', 'parent_task',
                  'assignee', 'completed_at', 'start_delta', 'duration', 'status')
        read_only_fields = ('id', 'workflow', 'parent_task',
                            'completed_at', 'status')

    def validate_assignee(self, assignee):
        '''
        Validated that assignee belongs to the same company as of the user and is an active employee
        '''
        employee = self.context['request'].user.active_employee
        if not assignee.company == employee.company:
            raise serializers.ValidationError(generate_error(
                'New assignee must be of the same company'))
        if not assignee.is_active:
            raise serializers.ValidationError(
                generate_error('Assignee must be an active employee'))

        return assignee


class TaskUpdateSerializer(TaskBaseSerializer):
    class Meta(TaskBaseSerializer.Meta):
        pass

    def validate_start_delta(self, value):
        '''
        validates that start delta could not be updated for ongoing task and if parent task is completed.
        '''
        instance = self.instance
        if instance.status == common_constant.TASK_STATUS.ONGOING:
            raise serializers.ValidationError(generate_error(
                'start delta could not be updated for ongoing task'))

        delta_time = None
        if instance.parent_task and instance.parent_task.status == common_constant.TASK_STATUS.COMPLETE:
            delta_time = instance.parent_task.completed_at + \
                instance.start_delta - timezone.now()
        if not instance.parent_task and instance.workflow.status == common_constant.WORKFLOW_STATUS.INPROGRESS:
            delta_time = instance.workflow.start_at + instance.start_delta - timezone.now()

        if delta_time and delta_time < timedelta(hours=common_constant.TASK_START_UPDATE_THRESHOLD_HOURS):
            raise serializers.ValidationError(
                generate_error(
                    'could not update start delta as the task will start soon')
            )

        return value

    def validate_assignee(self, assignee):
        '''
        override to verify that user can not update assignee if user is only assignee and not admin or write accessor
        '''
        assignee = super(TaskUpdateSerializer,
                         self).validate_assignee(assignee)

        employee = self.context['request'].user.active_employee
        instance = self.instance

        isUserOnlyAssignee = instance.assignee == employee and not employee.is_admin
        isUserOnlyAssignee = isUserOnlyAssignee and (not employee.shared_workflows.filter(
            workflow=instance.workflow,
            permission=common_constant.PERMISSION.READ_WRITE
        ).exists())
        if isUserOnlyAssignee:
            raise serializers.ValidationError(
                generate_error(
                    'Assignee does not have permissions to update assignee of the task')
            )

        return assignee

    def validate(self, data):
        '''
        Check task time conflict if start_delta or duration is updated
        '''
        instance = self.instance

        if(data.get('start_delta') or data.get('duration')):
            task_start_time = data.get('start_delta', instance.start_delta)
            task_parent = instance.parent_task
            if(task_parent):
                task_start_time += get_parent_start_time(task_parent)
            else:
                task_start_time += instance.workflow.start_at
            task_end_time = task_start_time + \
                data.get('duration', instance.duration)
            employee = data.get('assignee', instance.assignee)
            if is_task_conflicting(employee, task_start_time, task_end_time, ignore_tasks_ids=[instance.id]):
                raise serializers.ValidationError(generate_error(
                    'Task time conflict occurred for user {email}'.format(
                        email=employee.user.email)
                ))

        return data


class WorkflowAccessBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowAccess
        fields = ('id', 'employee', 'permission')
        read_only_fields = ('id', )

    def validate_employee(self, employee):
        '''
        Validated that employee (accessor) belongs to the same company as of the user and is an active employee
        '''
        user = self.context['request'].user.active_employee
        if not employee.company == user.company:
            raise serializers.ValidationError(
                generate_error('Accessor must be of the same company'))
        if not employee.is_active:
            raise serializers.ValidationError(
                generate_error('Accessor must be an active employee'))

        return employee


class WorkflowAccessDestroySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowAccess
        fields = ('employee',)
        read_only_fields = ()


class WorkflowAccessCreateSerializer(WorkflowAccessBaseSerializer):
    class Meta(WorkflowAccessBaseSerializer.Meta):
        fields = WorkflowAccessBaseSerializer.Meta.fields + ('workflow',)
        read_only_fields = WorkflowAccessBaseSerializer.Meta.read_only_fields + \
            ('workflow',)
        extra_kwargs = {
            'permission': {
                'required': True
            }
        }

    @atomic
    def create(self, validated_data):
        '''
        override to create or update accessor instance and send mail.
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


class WorkflowAccessUpdateSerializer(serializers.Serializer):
    '''
        update the permission of workflow with this serializer.
    '''

    read_permissions = serializers.PrimaryKeyRelatedField(
        queryset=UserCompany.objects.all(),
        many=True
    )

    write_permissions = serializers.PrimaryKeyRelatedField(
        queryset=UserCompany.objects.all(),
        many=True
    )

    def validate_read_permissions(self, value):
        request = self.context['request']
        company = request.user.company
        if len(filter(lambda employee: employee.company != company, value)):
            raise serializers.ValidationError(
                'all employees must be active and belong to same company'
            )
        return value

    def validate_write_permissions(self, value):
        request = self.context['request']
        company = request.user.company
        if len(filter(lambda employee: employee.company != company, value)):
            raise serializers.ValidationError(
                'all employees must be active and belong to same company'
            )
        return value

    def validate(self, attr):
        read_permissions = attr['read_permissions']
        write_permissions = attr['write_permissions']

        # check for instersection.
        s_read_permission = set(read_permissions)
        if len([perm for perm in write_permissions if perm in s_read_permission]):
            raise serializers.ValidationError(
                generate_error('permissions must be exclusive')
            )
        return attr

    @atomic
    def update(self, workflow, validated_data):
        read_permissions = validated_data['read_permissions']
        write_permissions = validated_data['write_permissions']

        all_permissions = WorkflowAccess.objects.filter(workflow=workflow)

        existing_updatable_permissions = all_permissions.filter(
            Q(
                employee__in=read_permissions,
                permission=common_constant.PERMISSION.READ_WRITE
            ) | Q(
                employee__in=write_permissions,
                permission=common_constant.PERMISSION.READ
            )
        )

        existing_non_updatable_permission = all_permissions.filter(
            Q(
                employee__in=read_permissions,
                permission=common_constant.PERMISSION.READ
            ) | Q(
                employee__in=write_permissions,
                permission=common_constant.PERMISSION.READ_WRITE
            )
        )

        delete_permissions = all_permissions.filter(
            ~Q(
                employee__in=read_permissions
            ) & ~Q(
                employee__in=write_permissions
            )
        )
        # improve performance
        read_permissions = set(read_permissions)
        write_permissions = set(write_permissions)
        # Update Permission instance.
        for permission in existing_updatable_permissions:
            if permission.employee in read_permissions:
                permission.permission = common_constant.PERMISSION.READ
                read_permissions.remove(permission.employee)
            else:
                permission.permission = common_constant.PERMISSION.READ_WRITE
                write_permissions.remove(permission.employee)

        for permission in existing_non_updatable_permission:
            if permission.employee in read_permissions:
                read_permissions.remove(permission.employee)
            else:
                write_permissions.remove(permission.employee)

        for permission in delete_permissions:
            permission.is_active = False

        new_permissions = [
            WorkflowAccess(
                workflow=workflow,
                employee=employee,
                permission=common_constant.PERMISSION.READ
            )
            for employee in read_permissions
        ]
        new_permissions.extend(
            [
                WorkflowAccess(
                    workflow=workflow,
                    employee=employee,
                    permission=common_constant.PERMISSION.READ_WRITE
                )
                for employee in write_permissions
            ]
        )

        logger.debug('delete permission {}'.format(delete_permissions))
        logger.debug(
            'existing permission {}'.format(
                existing_updatable_permissions
            )
        )
        logger.debug('new_permissions {}'.format(new_permissions))

        # create history
        update_bulk_history([per for per in existing_updatable_permissions])

        delete_bulk_history([per for per in delete_permissions])
        # db operations
        bulk_update(
            delete_permissions,
            update_fields=['is_active']
        )
        bulk_update(
            existing_updatable_permissions,
            update_fields=['permission']
        )
        new_instances = WorkflowAccess.objects.bulk_create(new_permissions)

        create_bulk_history([per for per in new_instances])

        send_permission_mail.delay(map(lambda x: x.id, new_instances))

        return new_instances


class WorkflowBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ('id', 'template', 'name', 'creator',
                  'start_at', 'completed_at', 'status')
        read_only_fields = ('id', 'creator', 'completed_at', 'status')

    def validate_start_at(self, start_at):
        '''
        Validate the start date and time is after current date and time.
        '''
        if start_at < timezone.now():
            raise serializers.ValidationError(generate_error(
                'start date can not be earlier than current time.'))

        return start_at


class WorkflowCreateSerializer(WorkflowBaseSerializer):
    tasks = TaskBaseSerializer(many=True)
    accessors = WorkflowAccessBaseSerializer(many=True)

    class Meta(WorkflowBaseSerializer.Meta):
        fields = WorkflowBaseSerializer.Meta.fields + ('tasks', 'accessors')

    def validate(self, data):
        '''
        Validate that tasks of assignees don't conflict with their other tasks.
        '''
        tasks = data.get('tasks', [])
        visited_assignees = {}
        prev_task_end_time = data['start_at']
        for task in tasks:
            task_start_time = prev_task_end_time + task['start_delta']
            task_end_time = task_start_time + task['duration']
            employee = task['assignee']
            if is_task_conflicting(employee, task_start_time, task_end_time, visited_assignees):
                raise serializers.ValidationError(generate_error(
                    'Task time conflict occurred for user {email}'.format(
                        email=employee.user.email)
                ))

            prev_task_end_time = task_end_time

        return data

    @atomic
    def create(self, validated_data):
        '''
        override due to nested writes. Also start workflow if it's start time delta is less than celery scheduled task
        schedule
        '''

        tasks = validated_data.pop('tasks', [])
        accessors = validated_data.pop('accessors', [])

        employee = self.context['request'].user.active_employee
        people_assiciated = {}
        people_assiciated[employee.id] = {'employee': employee,
                                          'is_creator': True}

        workflow = Workflow.objects.create(creator=employee, **validated_data)

        prev_task = None
        for task in tasks:
            prev_task = Task.objects.create(
                workflow=workflow, parent_task=prev_task, **task)
            # prev task Id required, bulk query ommited.
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
            instance = WorkflowAccess.objects.create(
                workflow=workflow, **accessor)
            person = people_assiciated.get(instance.employee_id, {})
            if not person:
                person['employee'] = instance.employee
                people_assiciated[instance.employee_id] = person
            person['is_shared'] = True
            person['write_permission'] = instance.permission == common_constant.PERMISSION.READ_WRITE

        workflow.send_mail(people_assiciated, is_updated=False)

        # if workflow will start before celery scheduled task, send it's start task to celery
        current_time = timezone.now()
        delta_time = workflow.start_at - current_time
        if(delta_time < timedelta(seconds=common_constant.WORKFLOW_PERIODIC_TASK_SCHEDULE_SECONDS)):
            workflow.status = common_constant.WORKFLOW_STATUS.SCHEDULED
            workflow.save()
            eta = workflow.start_at if workflow.start_at > current_time else timezone.now() + \
                timedelta(seconds=10)
            start_workflow.apply_async((workflow.id,), eta=eta)

        return workflow


class WorkflowUpdateSerializer(WorkflowBaseSerializer):
    '''
    Serializer for updating workflow basic details.
    '''
    class Meta(WorkflowBaseSerializer.Meta):
        read_only_fields = WorkflowBaseSerializer.Meta.read_only_fields + \
            ('template',)

    def validate_start_at(self, value):
        '''
        override to check that user can't update start time within few hours of workflow start time.
        '''
        value = super(WorkflowUpdateSerializer, self).validate_start_at(value)

        instance = self.instance
        if not instance.status == common_constant.WORKFLOW_STATUS.INITIATED:
            raise serializers.ValidationError(generate_error(
                'cannot update start at as workflow is in progress.'))

        if instance.start_at - timezone.now() < timedelta(hours=common_constant.WORKFLOW_START_UPDATE_THRESHOLD_HOURS):
            raise serializers.ValidationError(
                generate_error(
                    'could not update start time as workflow will start soon')
            )

        return value
