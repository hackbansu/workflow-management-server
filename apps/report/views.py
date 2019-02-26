# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from rest_framework import mixins, response, status, views, viewsets
from rest_framework.response import Response

from apps.common import constant as common_constant
from apps.company.models import UserCompany
from apps.company.permissions import IsCompanyAdmin


class EmployeeIJL(views.APIView):
    permission_classes = (IsCompanyAdmin,)

    def get(self, request, format=None):
        '''
        Returns number of users invited, joined and left company within 12 months (month wise)
        '''
        user = request.user
        company = user.company

        UserCompany.objects.filter(company=company,
                                   status=common_constant.USER_STATUS.INVITED)
