# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class WorkflowConfig(AppConfig):
    name = 'apps.workflow'

    def ready(self):
        import apps.workflow.signals
        import apps.history.signals
