# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import CICharField
from django.db import models

from apps.common.constant import TASK_STATUS, PERMISSION
from apps.workflow_template.models import WorkflowTemplate

User = get_user_model()


class Workflow(models.Model):
    '''
    Workflow model.
    '''
    template = models.ForeignKey(to=WorkflowTemplate, on_delete=models.PROTECT)
    name = CICharField(max_length=256)
    creator = models.ForeignKey(to=User, on_delete=models.PROTECT)
    start_at = models.DateTimeField()
    completed_at = models.DateTimeField(
        null=True, help_text='time when workflow completed')
    duration = models.DurationField(default=timedelta(
        0), help_text='expected completion duration')

    def __unicode__(self):
        return '{workflow_name}-#-{creator}'.format(
            workflow_name=self.name,
            creator=self.creator_id)


class Task(models.Model):
    '''
    Tasks in workflows.
    '''
    TASK_STATUS_CHOICES = (choice for choice in zip(
        TASK_STATUS, TASK_STATUS._fields))

    workflow = models.ForeignKey(to=Workflow, on_delete=models.CASCADE)
    title = CICharField(max_length=256)
    description = models.TextField(blank=True, default='')
    parent_task = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, related_name='child')
    assigne = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='tasks')
    completed_at = models.DateTimeField(null=True)
    start_delta = models.DurationField(
        default=timedelta(0),
        help_text='time delay between completion of parent task and star of current task')
    status = models.PositiveIntegerField(
        choices=TASK_STATUS_CHOICES, default=TASK_STATUS.UPCOMMING)

    def __unicode__(self):
        return '{workflow_id}-#-{title}'.format(
            title=self.title,
            workflow_id=self.workflow_id)


class WorkflowAccess(models.Model):
    '''
    Workflow accees permissions.
    '''
    WORKFLOW_PERMISSION_CHOICES = (
        choice for choice in zip(PERMISSION, PERMISSION._fields))
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    permission = models.PositiveIntegerField(
        choices=WORKFLOW_PERMISSION_CHOICES, default=PERMISSION.READ)

    class Meta:
        unique_together = ('user', 'workflow')

    def __unicode__(self):
        return '{user_id}-#-{workflow_id}-#-{permission}'.format(
            user_id=self.user_id,
            workflow_id=self.workflow_id,
            permission=self.permission)
