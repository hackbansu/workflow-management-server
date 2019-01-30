# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import CITextField, CICharField

from partial_index import PartialIndex, PQ

User = get_user_model()

DESIGNATION_CHOICES = {
    'HR': 0,
    'CEO': 1,
    'CTO': 2,
    'SDE-1': 3,
    'SDE-2': 4,
}

STATUS_CHOICES = {
    'INVITED': 0,
    'ACTIVE': 1,
    'INACTIVE': 2
}

LINK_NAME_CHOICES = {
    'TWITTER': 0,
    'FACEBOOK': 1,
    'GOOGLE': 2
}


class BaseModel(models.Model):
    '''
    Abstract model to provide created and modified fields.
    '''
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Company(BaseModel):
    '''
    All registered companies.
    '''
    company_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, verbose_name='company id')
    name = CICharField(unique=True, max_length=100, null=False, blank=False)
    address = CITextField( null=False, blank=False)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    logo = models.ImageField(upload_to='company/logo/')

    def __unicode__(self):
        return self.name

class Link(BaseModel):
    '''
    Social links of companies
    '''
    NAME_CHOICES_TUP = ((value, key) for (key, value) in LINK_NAME_CHOICES.iteritems() )

    company = models.ForeignKey(
        to=Company, on_delete=models.CASCADE, related_name='links')
    name = models.PositiveIntegerField(choices=NAME_CHOICES_TUP)
    url = models.URLField()

    class Meta:
        unique_together=('company', 'name')

    def __unicode__(self):
        return '{}-#-{}'.format(self.company.name, self.name)


class UserCompany(BaseModel):
    '''
    Model holding employees of companies
    '''
    DESIGNATION_CHOICES_TUP = ((value, key)
                               for (key, value) in DESIGNATION_CHOICES.iteritems() )
    STATUS_CHOICES_TUP = ((value, key) for (key, value) in STATUS_CHOICES.iteritems() )

    user = models.ForeignKey(
        to=User, on_delete=models.PROTECT, related_name='companies')
    company = models.ForeignKey(
        to=Company, on_delete=models.PROTECT, related_name='users')
    designation = models.PositiveIntegerField(choices=DESIGNATION_CHOICES_TUP)
    join_on = models.DateTimeField()
    inactive_on = models.DateTimeField(null=True)
    status = models.PositiveIntegerField(choices=STATUS_CHOICES_TUP)
    is_admin = models.BooleanField(default=False)

    class Meta:
        indexes = [
            PartialIndex(fields=['user', 'company'], unique=True, where=
            PQ(status__in=(STATUS_CHOICES['INVITED'],STATUS_CHOICES['ACTIVE'])) )
        ]

    def __unicode__(self):
        return '{}-#-{}-#-{}'.format(self.user.name, self.company.name, self.status)

