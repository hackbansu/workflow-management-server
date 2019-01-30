# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import CICharField
from django.contrib.auth import get_user_model

from apps.workflow_template.models import WorkflowTemplate

User = get_user_model()

TASK_STATUS_CHOICES={
    'UPCOMMING': 0,
    'ONGOING' : 1,
    'COMPLETED' : 2
}

WORKFLOW_PERMISSION_CHOICES = {
    'READ' : 0,
    'READ_WRITE' : 1
}

class Workflow(models.Model):
    '''
    Workflow model.
    '''
    template = models.ForeignKey(to=WorkflowTemplate, on_delete=models.PROTECT)
    name = CICharField( max_length=100, null=False, blank=False)
    creator = models.ForeignKey(to= User, on_delete=models.PROTECT )
    start_time = models.DateTimeField()
    is_completed = models.BooleanField()
    expected_end_time = models.DateTimeField()
    def __unicode__(self):
        return '{}-#-{}'.format(self.name, self.creator.name )


class Task(models.Model):
    '''
    Tasks in workflows.
    '''
    TASK_STATUS_CHOICES_TUP = ((value, key) for (key, value) in TASK_STATUS_CHOICES.iteritems() )
    workflow = models.ForeignKey(to=Workflow, on_delete=models.CASCADE)
    title = CICharField( max_length=100, null=False, blank=False)
    description = models.TextField( null=False, blank=False)
    parent_task = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name='childs')
    child_task = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name='parents')
    assigned_to = models.ForeignKey(User, on_delete=models.PROTECT, related_name='tasks')
    delta_time = models.DurationField(help_text='time delay between completion of parent task and star of current task')
    status = models.PositiveIntegerField(choices=TASK_STATUS_CHOICES_TUP)

    class Meta:
        unique_together = ('workflow', 'title')

    def __unicode__(self):
        return '{}-#-{}-#-{}'.format(self.title, self.workflow.name, self.assigned_to.name )


class WorkflowAccess(models.Model):
    '''
    Workflow accees permissions.
    '''
    WORKFLOW_PERMISSION_CHOICES_TUP = ((value, key) for (key, value) in WORKFLOW_PERMISSION_CHOICES.iteritems() )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    permission = models.PositiveIntegerField(choices=WORKFLOW_PERMISSION_CHOICES_TUP)

    class Meta:
        unique_together = ('user', 'workflow')

    def __unicode__(self):
        return '{}-#-{}-#-{}'.format(self.user.name, self.workflow.name, self.permission)
