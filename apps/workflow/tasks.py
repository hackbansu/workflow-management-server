# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import task, shared_task
from datetime import timedelta
import logging

from django.db.transaction import atomic
from django.utils import timezone

from apps.common import constant as common_constant
from apps.workflow.models import Workflow, Task, WorkflowAccess

logger = logging.getLogger(__name__)


@shared_task
@atomic
def start_workflow(workflow_id):
    '''
    Marks the workflow to be inprogress.
    Also start the first task if it's start delta is less than celery scheduled task schedule

    Arguments:
        workflow_id {int} -- id of the workflow to start
    '''

    workflow = Workflow.objects.get(pk=workflow_id)
    workflow.status = common_constant.WORKFLOW_STATUS.INPROGRESS
    workflow.save(update_fields=['status'])

    first_task = workflow.tasks.filter(parent_task__isnull=True)[0]
    if first_task.start_delta < timedelta(seconds=common_constant.TASK_PERIODIC_TASK_SCHEDULE_SECONDS):
        first_task.status = common_constant.TASK_STATUS.SCHEDULED
        first_task.save()
        start_task.apply_async(
            (first_task.id,),
            countdown=first_task.start_delta.seconds
        )


@shared_task
@atomic
def start_task(task_id):
    '''
    Marks the task as ongoing.

    Arguments:
        task_id {int} -- id of the task to start
    '''

    task = Task.objects.get(pk=task_id)
    task.status = common_constant.TASK_STATUS.ONGOING
    task.save(update_fields=['status'])


@shared_task
@atomic
def start_workflows_periodic():
    '''
    Periodic task to schedule workflows to start who's start time is below some threshold.
    '''
    current_time = timezone.now()
    workflows = Workflow.objects.filter(
        status=common_constant.WORKFLOW_STATUS.INITIATED,
        start_at__lt=current_time +
        timedelta(hours=common_constant.WORKFLOW_START_UPDATE_THRESHOLD_HOURS)
    )
    for workflow in workflows.all():
        eta = workflow.start_at if workflow.start_at > current_time else timezone.now() + \
            timedelta(seconds=10)
        start_workflow.apply_async((workflow.id,), eta=eta)

    workflows.update(status=common_constant.WORKFLOW_STATUS.SCHEDULED)


@atomic
def schedule_tasks_helper(tasks):
    '''
    Helper function for scheduling tasks.

    Arguments:
        tasks {QuerySet} -- queryset containing the tasks to check for their start time
    '''

    current_time = timezone.now()
    for task in tasks.all():
        if task.parent_task:
            delta_time = task.parent_task.completed_at + task.start_delta - current_time
        else:
            delta_time = task.workflow.start_at + task.start_delta - current_time

        if (delta_time < timedelta(hours=common_constant.TASK_START_UPDATE_THRESHOLD_HOURS)):
            if delta_time < timedelta(seconds=0):
                delta_time = timedelta(seconds=10)
            start_task.apply_async((task.id,), countdown=delta_time.seconds)
        else:
            tasks.exclude(pk=task.id)

    tasks.update(status=common_constant.TASK_STATUS.SCHEDULED)


@shared_task
def start_tasks_periodic():
    '''
    Periodic function to schedule tasks to start who's start time is below some threshold.
    '''

    # get tasks that have parent
    tasks = Task.objects.filter(status=common_constant.TASK_STATUS.UPCOMING,
                                parent_task__isnull=False,
                                parent_task__status=common_constant.TASK_STATUS.COMPLETE)
    schedule_tasks_helper(tasks)

    # get tasks that don't have parent, i.e. are first tasks of their workflows
    tasks = Task.objects.filter(status=common_constant.TASK_STATUS.UPCOMING,
                                parent_task__isnull=True,
                                workflow__status=common_constant.WORKFLOW_STATUS.INPROGRESS)
    schedule_tasks_helper(tasks)


@shared_task
def send_permission_mail(instances):
    instances = WorkflowAccess.objects.filter(id__in=instances)
    for instance in instances:
        instance.send_mail()


@shared_task
def send_mail_for_workflow(instance, update_fields):
    '''
    sends mail on workflow update.
    '''
    instance = Workflow.objects.get(id=instance)
    if instance.status == common_constant.WORKFLOW_STATUS.COMPLETE:
        instance.send_mail(
            associated_people_details=False, is_completed=True)
    elif update_fields:
        if 'status' in update_fields and instance.status == common_constant.WORKFLOW_STATUS.INPROGRESS:
            instance.send_mail(
                associated_people_details=False, is_started=True)
        elif 'status' in update_fields and instance.status == common_constant.WORKFLOW_STATUS.SCHEDULED:
            return
    else:
        instance.send_mail(associated_people_details=None, is_updated=True)


@shared_task
def send_mail_for_task(instance, update_fields):
    '''
    sends mail on task update.
    '''
    instance = Task.objects.get(pk=instance)
    if instance.status == common_constant.TASK_STATUS.COMPLETE:
        instance.send_mail(is_completed=True)
    elif update_fields:
        if 'status' in update_fields and instance.status == common_constant.TASK_STATUS.ONGOING:
            instance.send_mail(is_started=True)
        if 'status' in update_fields and instance.status == common_constant.TASK_STATUS.SCHEDULED:
            return
    else:
        instance.send_mail()
