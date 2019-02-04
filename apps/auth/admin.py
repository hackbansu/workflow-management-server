# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from apps.auth.models import User


class UserAdmin(admin.ModelAdmin):
    '''
    UserAdmin to be use with django admin app.
    '''
    list_display = ['email', 'id', 'first_name','last_name' ]

admin.site.register(User, UserAdmin)

