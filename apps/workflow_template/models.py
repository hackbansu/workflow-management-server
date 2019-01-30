# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import uuid

from django.db import models
from django.contrib.postgres.fields import JSONField, CICharField

class WorkflowTemplate(models.Model):
    template_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, verbose_name='template id')
    name = CICharField( max_length=100, null=False, blank=False)
    template = JSONField()

    def __unicode__(self):
        return self.name