# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import task, shared_task
from datetime import timedelta
import logging

from django.utils import timezone

from apps.common import constant as common_constant
from apps.workflow.models import Workflow, Task

logger = logging.getLogger(__name__)


@shared_task
def start_task(task):
    task.status = common_constant.TASK_STATUS.ONGOING
    task.save()


@shared_task
def start_workflow(workflow):
    workflow.status = common_constant.WORKFLOW_STATUS.INPROGRESS
    workflow.save()


@task
def start_workflows_periodic():
    current_time = timezone.now()
    logger.info('workflows periodic task executing')
    workflows = Workflow.objects.filter(start_at__lt=current_time + timedelta(
        hours=common_constant.WORKFLOW_START_UPDATE_THRESHOLD_HOURS
    ))
    for workflow in workflows.all():
        start_workflow.apply_async((workflow), eta=workflow.start_at)


@task
def start_tasks_periodic():
    logger.info('tasks periodic task executing')
    print "hey tasks"
    current_time = timezone.now()
    # get tasks that have parent
    tasks = Task.objects.filter(completed_at__isnull=True,
                                parent_task__isnull=False,
                                parent_task__status=common_constant.TASK_STATUS.COMPLETE)
    for task in tasks.all():
        delta_time = task.parent_task.completed_at + task.start_delta - current_time
        if (delta_time < timedelta(minutes=common_constant.TASK_START_UPDATE_THRESHOLD_MINUTES)):
            start_task.apply_async((task), countdown=delta_time)

    # get tasks that don't have parent, i.e. are first tasks of their workflows
    tasks = Task.objects.filter(completed_at__isnull=True,
                                parent_task__isnull=True,
                                workflow__status=common_constant.WORKFLOW_STATUS.INPROGRESS)
    for task in tasks.all():
        delta_time = task.workflow.start_at + task.start_delta - current_time
        if (delta_time < timedelta(minutes=common_constant.TASK_START_UPDATE_THRESHOLD_MINUTES)):
            start_task.apply_async((task), countdown=delta_time)
