# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.postgres.fields import JSONField, CICharField
from django.db import models


class WorkflowTemplate(models.Model):
    name = CICharField(max_length=100, unique=True)
    template = JSONField()

    def __unicode__(self):
        return self.name
