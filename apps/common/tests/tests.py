# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.test import APITestCase


class BaseTest(APITestCase):
    fixtures = [
        'apps/common/fixtures/workflow_auth.json',
        'apps/common/fixtures/company.json'
        ]
