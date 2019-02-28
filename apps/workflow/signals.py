from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.common import constant as common_constant
from apps.workflow.models import Workflow, Task


@receiver(post_save, sender=Workflow)
def send_mail_on_workflow_update(sender, instance, created, **kwargs):
    '''
    sends mail on workflow update.
    '''
    if not created:
        if instance.status == common_constant.WORKFLOW_STATUS.COMPLETE:
            instance.send_mail(associated_people_details=False, is_completed=True)
        elif kwargs['update_fields']:
            if 'status' in kwargs['update_fields'] and instance.status == common_constant.WORKFLOW_STATUS.INPROGRESS:
                instance.send_mail(associated_people_details=False, is_started=True)
            elif 'status' in kwargs['update_fields'] and instance.status == common_constant.WORKFLOW_STATUS.SCHEDULED:
                return
        else:
            instance.send_mail(associated_people_details=None, is_updated=True)


@receiver(post_save, sender=Task)
def send_mail_on_task_update(sender, instance, created, **kwargs):
    '''
    sends mail on task update.
    '''
    if not created:
        if instance.status == common_constant.TASK_STATUS.COMPLETE:
            instance.send_mail(is_completed=True)
        elif kwargs['update_fields']:
            if 'status' in kwargs['update_fields'] and instance.status == common_constant.TASK_STATUS.ONGOING:
                instance.send_mail(is_started=True)
            if 'status' in kwargs['update_fields'] and instance.status == common_constant.TASK_STATUS.SCHEDULED:
                return
        else:
            instance.send_mail()
