from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.common import constant as common_constant
from apps.workflow.models import Workflow, Task
from apps.workflow.tasks import send_mail_for_workflow, send_mail_for_task

# TODO : send mail via celery.


@receiver(post_save, sender=Workflow)
def send_mail_on_workflow_update(sender, instance, created, **kwargs):
    '''
    sends mail on workflow update.
    '''
    if not created:
        update_fields = kwargs.get('update_fields') or []
        send_mail_for_workflow.delay(instance.id, list(update_fields))


@receiver(post_save, sender=Task)
def send_mail_on_task_update(sender, instance, created, **kwargs):
    '''
    sends mail on task update.
    '''
    if not created:
        update_fields = kwargs.get('update_fields') or []
        send_mail_for_task.delay(instance.id, list(update_fields))
