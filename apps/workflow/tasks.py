from celery import shared_task
import logging

from apps.common import constant as common_constant

logger = logging.getLogger(__name__)


@shared_task
def start_task(task):
    task.status = common_constant.TASK_STATUS.ONGOING


@shared_task
def start_workflow(workflow):
    first_task = workflow.tasks.filter(parent_task__isnull=True)[0]
    start_task.apply_async((first_task), eta=workflow.start_task + first_task.start_delta)
