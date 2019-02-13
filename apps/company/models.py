# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid
import logging

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import CICharField

from partial_index import PartialIndex, PQ

from apps.common.models import BaseModel
from apps.common import constant as common_constant
from apps.common.helper import invite_token_generator

User = get_user_model()

logger = logging.getLogger(__name__)

def company_logo_dir(_, filename):
    '''
    company logo dir.
    '''
    return 'company/logo/{uuid}_{filename}'.format(
        uuid=uuid.uuid4(),
        filename=filename
    )


class Company(BaseModel):
    '''
    All registered companies.
    '''
    name = CICharField(unique=True, max_length=254, help_text='company name')
    address = models.CharField(max_length=254, help_text='company address')
    city = models.CharField(max_length=128, blank=True,
                            help_text='company city')
    state = models.CharField(max_length=128, blank=True,
                             help_text='company state')
    status = models.PositiveIntegerField(
        choices=(choice for choice in zip(
            common_constant.COMPANY_STATUS,
            common_constant.COMPANY_STATUS._fields
        )),
        default=common_constant.COMPANY_STATUS.UNVERIFIED,
        help_text='company status'
    )
    logo = models.ImageField(upload_to=company_logo_dir, blank=True)

    def __unicode__(self):
        return self.name

    def create_mail(self):
        '''
        company creation mail to admins.
        '''
        admins = self.user_companies.filter(
            is_admin=True,
            status=common_constant.USER_STATUS.ACTIVE
        )
        for admin in admins:
            context = {
                'name': admin.user.name,
                'company': self.name
            }
            admin.user.email_user(
                'company-create.txt',
                'company-create.html',
                'Company Registration', context
            )
            logger.info('creation mail send to %s '%(admin.user.email) )


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
        default=common_constant.LINK_TYPE.TWITTER,
        help_text='company link type'
    )
    url = models.URLField(help_text='link url')

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
        related_name='user_companies',
    )
    company = models.ForeignKey(
        to=Company,
        on_delete=models.PROTECT,
        related_name='user_companies'
    )
    designation = models.CharField(max_length=32)
    join_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
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
                where=PQ(status=common_constant.USER_STATUS.ACTIVE)
            )
        ]

    def __unicode__(self):
        return '{user}-#-{company}'.format(
            user=self.user_id,
            company=self.company_id
        )
    
    def get_invite_token(self):
        token = invite_token_generator.make_token(self.user, self)
        return '%s--%s--%s' % (token, self.user.id, self.id)

    def send_invite(self):
        '''
        send invitation mail.
        '''
        context = {
            'name': self.user.name,
            'token': self.get_invite_token(),
            'company': self.company
        }
        self.user.email_user(
            'invite-user.txt',
            'invite-user.html',
            'Invitation to join',
            context
        )
        logger.info('Invite mail send to {email}'.format(email=self.user.email))
