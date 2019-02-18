# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.viewsets import ModelViewSet GenericViewSet

from apps.workflow.models import Workflow
from apps.workflow.serializers import WorkflowSerializer


class WorkflowViews(ModelViewSet):
    serializer_class = WorkflowSerializer
    queryset = Workflow.objects.all()
