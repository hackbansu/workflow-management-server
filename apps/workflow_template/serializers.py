from __future__ import unicode_literals

import logging
from rest_framework import serializers

from apps.workflow_template.models import WorkflowTemplate


class WorkflowTemplateSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkflowTemplate
        fields = ('id', 'name', 'structure', 'thumbnail')
        read_only_fields = ('id', 'name', 'structure', 'thumbnail')
