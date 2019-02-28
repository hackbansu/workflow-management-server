# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid

from django.contrib.postgres.fields import JSONField, CICharField
from django.db import models


def logo_dir(_, filename):
    '''
    return template logo path.

    Arguments:
        _ {model instance} -- instance of the WorkflowTemplate model.
        filename {string} --  filename that was originally given to the file.
    '''
    return 'templates/logo/{uuid}-{filename}'.format(
        uuid=uuid.uuid4(),
        filename=filename
    )


class WorkflowTemplate(models.Model):
    name = CICharField(max_length=100, unique=True)
    structure = JSONField()
    logo = models.ImageField(
        upload_to=logo_dir,
        blank=True,
        help_text='Template logo picture'
    )

    def __unicode__(self):
        return self.name

    def _history_representation(self):
        '''
            method use for getting representation of object for history.
        '''
        return self.name
