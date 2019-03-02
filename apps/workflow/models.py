# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta
import logging

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import CICharField
from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

from partial_index import PartialIndex, PQ
from model_utils.tracker import FieldTracker

from apps.common import constant as common_constant
from apps.company.models import UserCompany
from apps.workflow_template.models import WorkflowTemplate
from apps.history.models import History

User = get_user_model()

logger = logging.getLogger(__name__)


class WorkflowAccessManager(models.Manager):
    def get_queryset(self):
        return super(WorkflowAccessManager, self).get_queryset().filter(is_active=True)


class Workflow(models.Model):
    '''
    Workflow model.
    '''
    template = models.ForeignKey(to=WorkflowTemplate, on_delete=models.PROTECT)
    name = CICharField(max_length=256)
    creator = models.ForeignKey(to=UserCompany, on_delete=models.PROTECT)
    start_at = models.DateTimeField()
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='time when workflow completed'
    )
    status = models.PositiveIntegerField(
        choices=(choice for choice in zip(
            common_constant.WORKFLOW_STATUS,
            common_constant.WORKFLOW_STATUS._fields
        )),
        default=common_constant.WORKFLOW_STATUS.INITIATED
    )

    tracker = FieldTracker(
        fields=['name', 'creator', 'start_at', 'completed_at', 'status'])

    histories = GenericRelation(History, related_query_name='workflows')

    def __unicode__(self):
        return '{workflow_name}-#-{creator}'.format(
            workflow_name=self.name,
            creator=self.creator_id
        )

    def send_mail(self, associated_people_details, is_updated=False, is_started=False, is_completed=False):
        '''
        send workflow created/shared/updated mail.
        '''
        if not associated_people_details:
            associated_people_details = {}
            associated_people_details[self.creator_id] = {
                'employee': self.creator}

            for accessor in self.accessors.all():
                associated_people_details[accessor.employee_id] = {
                    'employee': accessor.employee}
            for task in self.tasks.all():
                associated_people_details[task.assignee_id] = {
                    'employee': task.assignee}

        for key, person in associated_people_details.iteritems():
            context = {
                'is_updated': is_updated,
                'is_started': is_started,
                'is_completed': is_completed,
                'is_creator': person.get('is_creator', False),
                'is_shared': person.get('is_shared', False),
                'name': person['employee'].user.name,
                'workflow_name': self.name,
                'write_permission': person.get('write_permission', False),
                'task_list': person.get('task_list', [])
            }
            person['employee'].user.email_user(
                'workflow.txt',
                'workflow.html',
                'Workflow Update',
                context
            )
            logger.info('Workflow create/update/shared mail send to {email}'.format(
                email=person['employee'].user.email))

    def _history_representation(self):
        '''
            method use for getting representation of object for history.
        '''
        return self.name


class Task(models.Model):
    '''
    Tasks in workflows.
    '''
    workflow = models.ForeignKey(
        to=Workflow, on_delete=models.CASCADE, related_name='tasks')
    title = CICharField(max_length=256)
    description = models.TextField(blank=True, default='')
    parent_task = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        related_name='child',
        blank=True
    )
    assignee = models.ForeignKey(
        UserCompany,
        on_delete=models.PROTECT,
        related_name='tasks'
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    start_delta = models.DurationField(
        help_text='time delay between completion of parent task and star of current task'
    )
    duration = models.DurationField(
        help_text='expected duration of the task'
    )
    status = models.PositiveIntegerField(
        choices=(choice for choice in zip(
            common_constant.TASK_STATUS,
            common_constant.TASK_STATUS._fields
        )),
        default=common_constant.TASK_STATUS.UPCOMING
    )

    histories = GenericRelation(
        History,
        related_query_name='tasks'
    )

    # template id is intentionally excluded from tracking, if required first implement ._history_representation

    tracker = FieldTracker(
        fields=[
            'title', 'workflow', 'description',
            'parent_task', 'assignee', 'completed_at',
            'start_delta', 'duration', 'status'
        ]
    )

    def __unicode__(self):
        return '{workflow_id}-#-{title}'.format(
            title=self.title,
            workflow_id=self.workflow_id
        )

    def _history_representation(self):
        '''
            method use for getting representation of object for history.
        '''
        return self.title

    def send_mail(self, is_started=False, is_completed=False):
        '''
        send task start/update mail.
        '''
        context = {
            'task_title': self.title,
            'workflow_name': self.workflow.name,
            'name': self.assignee.user.name,
            'is_started': is_started,
            'is_completed': is_completed
        }

        # send mail to the assignee
        self.assignee.user.email_user(
            'task.txt', 'task.html', 'Task Update', context)
        logger.info(
            'Task start/update mail send to {email}'.format(email=self.assignee.user.email))

        # send mail to the  creator if task is updated
        context['name'] = self.workflow.creator.user.name
        self.workflow.creator.user.email_user(
            'task.txt', 'task.html', 'Task Update', context)
        logger.info(
            'Task start/update mail send to {email}'.format(email=self.assignee.user.email))


class WorkflowAccess(models.Model):
    '''
    Workflow accees permissions.
    '''
    employee = models.ForeignKey(
        UserCompany, on_delete=models.CASCADE, related_name='shared_workflows')
    workflow = models.ForeignKey(
        Workflow, on_delete=models.CASCADE, related_name='accessors')
    permission = models.PositiveIntegerField(
        choices=(choice for choice in zip(
            common_constant.PERMISSION,
            common_constant.PERMISSION._fields
        )),
        default=common_constant.PERMISSION.READ
    )

    tracker = FieldTracker(
        fields=[
            'employee', 'workflow', 'permission'
        ]
    )

    is_active = models.BooleanField(default=True)

    histories = GenericRelation(
        History,
        related_query_name='workflow_accesses'
    )

    objects = WorkflowAccessManager()

    objects_all = models.Manager()

    class Meta:
        indexes = [
            PartialIndex(
                fields=['employee', 'workflow'],
                unique=True,
                where=PQ(is_active=True)
            )
        ]
        # unique_together = ('employee', 'workflow')

    def __unicode__(self):
        return '{employee_id}-#-{workflow_id}-#-{permission}'.format(
            employee_id=self.employee_id,
            workflow_id=self.workflow_id,
            permission=self.permission
        )

    def _history_representation(self):
        '''
            method use for getting representation of object for history.
        '''
        return '%s --> %s' % (self.employee._history_representation(), self.workflow._history_representation())

    def send_mail(self):
        '''
        send workflow shared mail.
        '''
        context = {
            'is_updated': False,
            'is_creator': False,
            'is_shared': True,
            'name': self.employee.user.name,
            'workflow_name': self.workflow.name,
            'write_permission': self.permission == common_constant.PERMISSION.READ_WRITE,
            'task_list': []
        }
        self.employee.user.email_user(
            'workflow.txt',
            'workflow.html',
            'Workflow Update',
            context
        )
        logger.info(
            'Accessor create/update mail send to {email}'.format(email=self.employee.user.email))
