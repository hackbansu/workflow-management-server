# pylint:disable=E1101
# pylint:disable=W0221
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as ParentUserManager
from django.contrib.postgres.fields import CIEmailField
from django.db import models
from rest_framework.authtoken.models import Token


class UserManager(ParentUserManager):
    '''
    UserManger is the extension of inbuilt UserManager of Abstract User.
    It is created to completely remove username from database and handle
    creation of user operation without username.
    Email is treated as unique username field.
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
        '''
        Overrider to effectively remove usename field.
        '''
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        '''
        Overrider to effectively remove usename field.
        '''
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


def usr_profil_dir(_, filename):
    '''
    return profile photo save path
    '''
    return 'user/profile/{uuid}-{filename}'.format(
        uuid=uuid.uuid4(),
        filename=filename)


class User(AbstractUser):
    '''
    User model is extention of AbstractUser
    providing basic details of for user.
    '''
    username = None
    first_name = models.CharField(max_length=128)
    email = CIEmailField(unique=True)
    profile_photo = models.ImageField(upload_to=usr_profil_dir)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    @property
    def name(self):
        'full name of user.'
        return '{first_name} {last_name}'.format(
            first_name=self.first_name,
            last_name=self.last_name)

    @property
    def token(self):
        'user auth token'
        return Token.objects.get_or_create(user=self)[0].key
