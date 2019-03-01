# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import CICharField

from apps.common.models import BaseModel
from apps.common import constant as common_constant


class History(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()
    field_name = CICharField(max_length=254)
    prev_value = models.TextField()
    next_value = models.TextField()
    action = models.PositiveIntegerField(
        choices=(choice for choice in zip(
            common_constant.HISTORY_ACTION,
            common_constant.HISTORY_ACTION._fields
        )),
        help_text='history action'
    )
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '{content_type}-#-{field_name}'.format(content_type=self.content_type, field_name=self.field_name)

    def _get_field(self):
        return self.content_type.model_class()._meta.get_field(self.field_name)

    def _get_related_model_class(self, field):
        return field.rel.to

    def _related_field_representation(self, field, value):
        model_class = self._get_related_model_class(field)
        # try:
        related_instance = model_class.objects.get(pk=value)
        return related_instance._history_representation()
        # except model_class.DoesNotExist:
        #     return value

    def _choice_field_representation(self, field, value):
        value = int(value)
        choices = dict(field.choices)
        # return choices.get(value, value)
        return choices[value]

    def _get_display_value(self, value):
        if value == 'None' or value is None:
            return value
        field = self._get_field()
        if field.get_internal_type() == 'ForeignKey':
            return self._related_field_representation(field, value)
        elif len(field.choices) > 0:
            return self._choice_field_representation(field, value)
        else:
            print 'unknown type'
            print field.get_internal_type()
            return value

    def get_prev_value_display(self):
        return self._get_display_value(self.prev_value)

    def get_next_value_display(self):
        return self._get_display_value(self.next_value)

    def get_content_object_display(self):
        if self.content_object is not None:
            return self.content_object._history_representation()
        return 'None'
