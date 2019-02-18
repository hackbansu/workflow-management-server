from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from apps.common import constant as common_constant

User = get_user_model()


