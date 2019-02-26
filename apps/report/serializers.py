# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers


class IJLEmployeeCountSerializer(serializers.Serializer):
    count = serializers.IntegerField(min_value=0)
    month = serializers.DateTimeField()
