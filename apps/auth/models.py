# pylint:disable=E1101
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid
import re

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as ParentUserManager
from django.contrib.postgres.fields import CIEmailField

from django.db import models
from rest_framework.authtoken.models import Token


class UserManager(ParentUserManager):
    '''
    UserManger is the extension of inbuilt UserManager of Abstract User.
    It is created to completely remove username from database and handle
    creation of user operation without username. Email is treated as unique username field.
    '''

    def _create_user(self, email, password, **extra_fields):
        '''
        Creates and saves a User with the given email and password.
        '''

        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        # username = self.model.normalize_username(username)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User (AbstractUser):
    '''
    User model is extention of AbstractUser provideing basic details of for user.
    '''
    user_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, verbose_name='user id')
    username = None
    first_name = models.CharField(
        blank=False, max_length=30, verbose_name='first name')
    email = CIEmailField(blank=False, unique=True)
    profile_photo = models.ImageField(upload_to='user/profile')
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def clean_email(self):
        return self.cleaned_data['email'].lower()

    @property
    def name(self):
        return '{} {}'.format(self.first_name, self.last_name)

    @property
    def token(self):
        return Token.objects.get_or_create(user=self)[0].key
    
    def __unicode__(self):
        return '{}-#-{}'.format(self.name, self.email)
