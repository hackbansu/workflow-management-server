# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from apps.company.models import Company, UserCompany, Link, UserCompanyCsv


class CompanyAdmin(admin.ModelAdmin):
    '''
    CompanyAdmin to be use with django admin app.
    '''
    list_display = ('id', 'name', 'address', 'city', 'state', 'logo', 'status')


class UserCompanyAdmin(admin.ModelAdmin):
    '''
    UserCompanyAdmin to be use with django admin app.
    '''
    list_display = ('id', 'user', 'company',
                    'designation', 'status', 'join_at', 'is_admin')


class LinkAdmin(admin.ModelAdmin):
    '''
    LinkAdmin to be use with django admin app.
    '''
    list_display = ('id', 'company', 'link_type', 'url')


class UserCompanyCsvAdmin(admin.ModelAdmin):
    '''
    UserCompanyCsvAdmin to be use with django admin app.
    '''
    list_display = ('id', 'user_company', 'csv_file', 'status')


admin.site.register(Company, CompanyAdmin)
admin.site.register(UserCompany, UserCompanyAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(UserCompanyCsv, UserCompanyCsvAdmin)
