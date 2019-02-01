# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import CICharField

from partial_index import PartialIndex, PQ

from apps.common.models import BaseModel
from apps.common import constant as common_constant

User = get_user_model()


def company_logo_dir(_, filename):
    return 'company/logo/{uuid}_{filename}'.format(
        uuid=uuid.uuid4(),
        filename=filename
    )


class Company(BaseModel):
    '''
    All registered companies.
    '''
    name = CICharField(unique=True, max_length=256)
    address = models.CharField(max_length=256)
    city = models.CharField(max_length=128, blank=True)
    state = models.CharField(max_length=128, blank=True)
    status = models.PositiveIntegerField(
        choices=(choice for choice in zip(
            common_constant.COMPANY_STATUS,
            common_constant.COMPANY_STATUS._fields
        )),
        default=common_constant.COMPANY_STATUS.UNVERIFIED
    )
    logo = models.ImageField(upload_to=company_logo_dir)

    def __unicode__(self):
        return self.name


class Link(BaseModel):
    '''
    Social links of companies
    '''
    company = models.ForeignKey(
        to=Company,
        on_delete=models.CASCADE,
        related_name='links'
    )
    link_type = models.PositiveIntegerField(
        choices=(choice for choice in zip(
            common_constant.LINK_TYPE,
            common_constant.LINK_TYPE._fields
        )),
        default=common_constant.LINK_TYPE.TWITTER
    )
    url = models.URLField()

    class Meta:
        unique_together = ('company', 'link_type')

    def __unicode__(self):
        return '{company}-#-{status}'.format(
            company=self.company_id,
            status=self.get_link_type_display()
        )


class UserCompany(BaseModel):
    '''
    Model holding employees of companies
    '''
    user = models.ForeignKey(
        to=User,
        on_delete=models.PROTECT,
        related_name='usercompanies'
    )
    company = models.ForeignKey(
        to=Company,
        on_delete=models.PROTECT,
        related_name='user_companies'
    )
    designation = models.CharField()
    join_at = models.DateTimeField(null=True, default=None)
    left_at = models.DateTimeField(null=True, default=None)
    status = models.PositiveIntegerField(
        choices=(choice for choice in zip(
            common_constant.USER_STATUS,
            common_constant.USER_STATUS._fields
        )),
        default=common_constant.USER_STATUS.INVITED
    )
    is_admin = models.BooleanField(default=False)

    class Meta:
        indexes = [
            PartialIndex(
                fields=['user', 'company'],
                unique=True,
                where=PQ(
                    status__in=(
                        common_constant.USER_STATUS.INVITED,
                        common_constant.USER_STATUS.INACTIVE
                    )
                )
            )
        ]

    def __unicode__(self):
        return '{user}-#-{company}'.format(
            user=self.user_id,
            company=self.company_id
        )
