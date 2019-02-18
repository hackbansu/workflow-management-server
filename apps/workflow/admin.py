# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from apps.workflow.models import Workflow, Task, WorkflowAccess


class WorkflowAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'creator', 'start_at', 'complete_at', 'duration')


class TaskAdmin(admin.ModelAdmin):
    list_display = tuple(field.name for field in Task._meta.get_fields())


class WorkflowAccessAdmin(admin.ModelAdmin):
    list_display = tuple(field.name for field in WorkflowAccess._meta.get_fields())


admin.site.register(Workflow, WorkflowAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(WorkflowAccess, WorkflowAccessAdmin)
