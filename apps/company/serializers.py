from __future__ import unicode_literals

from django.contrib.admin.utils import lookup_field
from django.contrib.auth import get_user_model
from jinja2.nodes import args_as_const
from rest_framework import serializers
from rest_framework.serializers import LIST_SERIALIZER_KWARGS

from apps.auth.serializers import InviteUserSerializer, UserAuthSerializer
from apps.auth.views import common_constant
from apps.common import constant as common_constant
from apps.company.models import Company, UserCompany

User = get_user_model()


class LinkSerializer(serializers.ModelSerializer):
    link_type_choices = serializers.SerializerMethodField()

    def get_link_type(self):
        return [{'display': key, 'value': value} for (key, value) in zip(common_constant.LINK_TYPE._fields, common_constant.LINK_TYPE)]

    class Meta:
        model = Company
        fields = fields = ('link_type_choices', 'link_type', 'url')
        extra_kwargs = {
            'link_type': {
                'help_text': 'company link type'
            },
            'url': {
                'help_text': 'link url'
            }
        }


class CompanySerializer(serializers.ModelSerializer):
    '''
    company.Company model serializer.
    '''
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return obj.get_status_display()

    def validate_name(self, value):
        qs = Company.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance)
        if qs.exists():
            raise serializers.ValidationError(
                {
                    'detail': 'This company name is already taken'
                }
            )
        return value

    class Meta:
        model = Company
        fields = (
            'id', 'name', 'address', 'city',
            'state', 'logo', 'status', 'links'
        )
        extra_kwargs = {
            'id': {
                'read_only': True,
                'help_text': 'unique company id'
            },
            'name': {
                'help_text': 'company name'
            },
            'address': {
                'help_text': 'company address'
            },
            'city': {
                'help_text': 'company city'
            },
            'state': {
                'help_text': 'company state'
            },
            'logo': {
                'help_text': 'company logo'
            },
            'links': {
                'required': False
            }
        }


class OldUserCompanySerializer(serializers.ModelSerializer):
    '''
    Company employee serializers.
    '''
    company = CompanySerializer()
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return obj.get_status_display()

    def validate(self, attr):
        user = self.context.get('user', None)
        if user:
            qs = UserCompany.objects.filter(
                user=user,
                status__in=[
                    common_constant.USER_STATUS.ACTIVE,
                    common_constant.USER_STATUS.INVITED
                ]
            )
            if qs.exists():
                raise serializers.ValidationError(
                    {'detail': 'You are already part of a company'})
        else:
            raise serializers.ValidationError(
                {'detail': 'User not in context'})
        return attr

    def create(self, validated_data):
        user = validated_data.pop('user', None)
        user = self.context.get('user') if user is None else user

        company = validated_data.pop('company')

        user = User.objects.create_user(**user)
        company = Company.objects.create(**company)
        instance = self.Meta.model.objects.create(
            user=user, company=company, is_admin=True, **validated_data)

        user.email_user(
            message='''
            Congratulations {user_name}
            
            Your company {company_name} is successfully created and pending for internal verification.
            We will inform you once done.

            Workflow Platform
            ''',
            **common_constant.NEW_COMPANY_EMAIL
        )

        return instance

    class Meta:
        model = UserCompany
        fields = [
            'company', 'is_admin',
            'designation', 'join_at', 'status'
        ]
        extra_kwargs = {
            'join_at': {
                'read_only': True
            },
            'designation': {
                'required': True
            },
            'is_admin': {
                'read_only': True
            }
        }


class UserCompanySerializer(OldUserCompanySerializer):
    user = UserAuthSerializer()

    def validate(self, attr):
        return attr

    def create(self, validated_data):
        return super(UserCompanySerializer, self).create(validated_data)

    class Meta(OldUserCompanySerializer.Meta):
        fields = OldUserCompanySerializer.Meta.fields
        fields += ['user']


class InviteEmployeeSerializer(OldUserCompanySerializer):
    user = InviteUserSerializer()
    def validate(self, attr):

        self.context.get('company')

        qs = UserCompany.objects.filter(
            user__email_iexact=attr.get('user').get('email'),
            status__in=[
                common_constant.USER_STATUS.ACTIVE,
                common_constant.USER_STATUS.INVITED
            ]
        )
        if qs.exists():
            if qs.first().status == common_constant.USER_STATUS.ACTIVE:
                raise serializers.ValidationError(
                    {'detail': 'User already active in company'}
                )
            elif qs.first().status == common_constant.USER_STATUS.INVITED:
                raise serializers.ValidationError(
                    {'detail': 'User already invited'}
                )
            raise serializers.ValidationError(
                {'detail': 'Unexpected condition'}
            )
        return attr

    def create(self, validated_data):

        company = self.context.get('company')
        user = validated_data.pop('user')

        user = User.objects.create_user(
            password='DefaultPassword',
            is_active=False,
            **user
        )

        return UserCompany.objects.create(
            user=user,
            company=company,
            **validated_data
        )

    class Meta(OldUserCompanySerializer.Meta):
        fields = OldUserCompanySerializer.Meta.fields
        fields += ['user']
