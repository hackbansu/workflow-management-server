# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from django.db.models.signals import post_save

from apps.workflow.signals import send_mail_on_workflow_update, send_mail_on_task_update


class WorkflowConfig(AppConfig):
    name = 'apps.workflow'

    def ready(self):
        from apps.workflow.models import Workflow, Task
        post_save.connect(send_mail_on_workflow_update, sender=Workflow)
        post_save.connect(send_mail_on_task_update, sender=Task)
