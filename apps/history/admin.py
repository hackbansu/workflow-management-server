# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from apps.history.models import History

# Register your models here.


class HistoryAdmin(admin.ModelAdmin):
    '''
    History admin to be used with django admin app.
    '''
    list_display = ('id', 'content_type', 'object_id', 'content_object',
                    'field_name', 'prev_value', 'next_value', 'action', 'created')


admin.site.register(History, HistoryAdmin)
