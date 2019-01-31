# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class BaseModel(models.Model):
    '''
    Abstract model to provide created and modified fields.
    '''
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
