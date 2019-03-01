# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from apps.history.models import History


class HistorySerializer(serializers.ModelSerializer):
    action = serializers.CharField(
        read_only=True,
        source='get_action_display'
    )
    prev_value = serializers.SerializerMethodField()
    next_value = serializers.SerializerMethodField()
    content_object = serializers.CharField(
        read_only=True,
        source='get_content_object_display'
    )

    def get_prev_value(self, obj):
        return obj.get_prev_value_display()

    def get_next_value(self, obj):
        return obj.get_next_value_display()

    class Meta:
        model = History
        fields = (
            'id', 'field_name', 'prev_value',
            'next_value', 'content_object', 'action', 'created',
            'content_type'
        )
