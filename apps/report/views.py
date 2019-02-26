# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime, timedelta

from django.utils import timezone
from django.db.models import Count
from django.db.models import functions as db_functions

from rest_framework import generics, mixins, response, status, views, viewsets
from rest_framework.response import Response

from apps.common import constant as common_constant
from apps.company.models import UserCompany
from apps.company.permissions import IsCompanyAdmin
from apps.report.serializers import IJLEmployeeCountSerializer


class IJLEmployeeCount(generics.GenericAPIView):
    queryset = UserCompany.objects.all()
    serializer_class = IJLEmployeeCountSerializer
    permission_classes = (IsCompanyAdmin,)

    def get_queryset(self):
        company = self.request.user.company
        return self.queryset.filter(company=company)

    def get_monthly_count_data(self, employees):
        data = employees.annotate(
            month=db_functions.TruncMonth('join_at')
        ).values('month').annotate(count=Count('id')).values('count', 'month')
        return self.get_serializer(data, many=True).data

    def get(self, request, format=None):
        '''
        Returns number of users invited, joined and left company within 12 months (month wise)
        '''
        employees = self.get_queryset()
        past_12_months = timezone.now() - timedelta(days=365)
        response_data = {}

        # users who were invited to the company
        response_data['invited_users'] = self.get_monthly_count_data(employees.filter(created__gt=past_12_months))
        # users who joined the company
        response_data['joined_users'] = self.get_monthly_count_data(employees.filter(join_at__gt=past_12_months))
        # users who left the company
        response_data['left_users'] = self.get_monthly_count_data(employees.filter(left_at__gt=past_12_months))

        return Response(response_data, status=status.HTTP_200_OK)
