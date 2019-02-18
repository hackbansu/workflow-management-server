# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from apps.auth.serializers import UserBasicDetailSerializer
from apps.workflow.models import Workflow


class WorkflowSerializer(serializers.ModelSerializer):
    creator = UserBasicDetailSerializer()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    class Meta:
        model = Workflow
        fields = (
            'template', 'name', 'creator', 'start_at',
            'complete_at', 'duration', 'tasks'
        )
        read_only_fields = ('creator',)
