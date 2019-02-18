# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid

from django.contrib.postgres.fields import JSONField, CICharField
from django.db import models


def thumbnail_dir(_, filename):
    '''
    return thumbnail path.

    Arguments:
        _ {model instance} -- instance of the WorkflowTemplate model.
        filename {string} --  filename that was originally given to the file.
    '''
    return 'templates/thumbnails/{uuid}-{filename}'.format(
        uuid=uuid.uuid4(),
        filename=filename
    )


class WorkflowTemplate(models.Model):
    name = CICharField(max_length=100, unique=True)
    structure = JSONField()
    thumbnail = models.ImageField(
        upload_to=thumbnail_dir,
        blank=True,
        help_text='Template thumbnail picture'
    )

    def __unicode__(self):
        return self.name
