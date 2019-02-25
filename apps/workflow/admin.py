# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from apps.workflow.models import Workflow, Task, WorkflowAccess


class WorkflowAdmin(admin.ModelAdmin):
    '''
    workflow admin to be used with django admin app.
    '''
    list_display = ('id', 'template', 'name', 'creator', 'start_at', 'completed_at', 'status')


class TaskAdmin(admin.ModelAdmin):
    '''
    Task admin to be used with django admin app.
    '''
    list_display = ('id', 'title', 'description', 'workflow', 'parent_task', 'assignee', 'status')


class WorkflowAccessAdmin(admin.ModelAdmin):
    '''
    Workflow access admin to be used with django admin app.
    '''
    list_display = ('id', 'employee', 'workflow', 'permission')


admin.site.register(Workflow, WorkflowAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(WorkflowAccess, WorkflowAccessAdmin)
