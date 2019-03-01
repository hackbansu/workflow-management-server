import logging
from django.db.models.signals import pre_save, pre_delete, post_save
from django.dispatch import receiver

from apps.workflow.models import Workflow, WorkflowAccess, Task
from apps.history.models import History
from apps.history.helpers import create_history, update_history, delete_history

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Workflow)
@receiver(post_save, sender=WorkflowAccess)
@receiver(post_save, sender=Task)
def track_history_for__create(sender, instance, created, **kwargs):
    if created:
        create_history(instance)


@receiver(pre_save, sender=Workflow)
@receiver(pre_save, sender=WorkflowAccess)
@receiver(pre_save, sender=Task)
def track_history_for_update(sender, instance, **kwargs):
    if not instance._state.adding:
        update_history(instance)


@receiver(pre_delete, sender=Workflow)
@receiver(pre_delete, sender=WorkflowAccess)
@receiver(pre_delete, sender=Task)
def track_history_for_delete(sender, instance, **kwargs):
    delete_history(instance)
