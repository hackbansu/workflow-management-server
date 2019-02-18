from __future__ import unicode_literals

import logging
from rest_framework import serializers

from apps.workflow_template.models import WorkflowTemplate as WorkflowTemplate


class WorkflowTemplateBaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkflowTemplate
        fields = ('id', 'name')
        read_only_fields = ('id', 'name')


class WorkflowTemplateSerializer(WorkflowTemplateBaseSerializer):

    class Meta(WorkflowTemplateBaseSerializer.Meta):
        fields = WorkflowTemplateBaseSerializer.Meta.fields + ('structure', 'logo')
        read_only_fields = WorkflowTemplateBaseSerializer.Meta.read_only_fields + ('structure', 'logo')
