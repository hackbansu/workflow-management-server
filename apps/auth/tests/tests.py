# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.test import APITestCase
from rest_framework.reverse import reverse

from apps.common.tests.tests import BaseTest 

class Login(BaseTest):
    
    def test_login(self):
        url = reverse('user-login')
        print url
        response = self.client.post(
            'url',
            {
                'email': 'test@t.com',
                'password': 'testpass'
            },
            format= 'json'
        )
        print response
        # self.assertTrue(False)
