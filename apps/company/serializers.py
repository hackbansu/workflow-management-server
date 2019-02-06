from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.auth.serializers import BaseUserSerializer, InviteUserSerializer, UserSerializer
from apps.common import constant as common_constant
from apps.company.models import Company, Link, UserCompany

User = get_user_model()


class LinkSerializer(serializers.ModelSerializer):
    '''
    Company link serializer.
    '''
    class Meta:
        model = Link
        fields = fields = ('link_type', 'url', 'company')
        extra_kwargs = {
            'link_type': {
                'help_text': 'company link type'
            },
            'url': {
                'help_text': 'link url'
            }
        },
        depth = 1


class CompanySerializer(serializers.ModelSerializer):
    '''
    Company model serializer.
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


class UserCompanySerializer(serializers.ModelSerializer):
    '''
    Create company with existing user.
    '''
    company = CompanySerializer()

    def get_user_instance(self, attr):
        user = self.context.get('request').user
        return user

    def get_user_company_qs(self, attr):
        user = self.get_user_instance(attr)
        return UserCompany.objects.filter(
            user_id=user.id,
            status__in=[
                common_constant.USER_STATUS.ACTIVE,
                common_constant.USER_STATUS.INVITED
            ]
        )

    def get_company_instance(self, attr):
        company = Company.objects.create(**attr.pop('company'))
        return company

    def validate(self, validated_data):
        qs = self.get_user_company_qs(validated_data)

        if qs.filter(status=common_constant.USER_STATUS.ACTIVE).exists():
            raise serializers.ValidationError(
                {'detail': 'User already part of a company'})

        if qs.filter(status=common_constant.USER_STATUS.INVITED).exists():
            raise serializers.ValidationError(
                {'detail': 'User already invited in a company'})
        return validated_data

    def create(self, validated_data):
        user = self.get_user_instance(validated_data)
        company = self.get_company_instance(validated_data)

        # just a safty precaution
        validated_data.pop('company', None)
        validated_data.pop('user', None)

        instance = UserCompany.objects.create(
            user=user,
            company=company,
            is_admin=True,
            status=common_constant.USER_STATUS.ACTIVE,
            **validated_data
        )
        user.company_create_mail(company.name)
        return instance

    class Meta:
        model = UserCompany
        fields = (
            'company', 'is_admin',
            'designation', 'status'
        )
        extra_kwargs = {

            'designation': {
                'required': True
            },
            'is_admin': {
                'read_only': True
            },
            'status': {
                'read_only': True
            }
        }


class UserCompanySignupSerializer(UserCompanySerializer):
    '''
    User Company serializer for simultaneous signup.
    '''
    user = UserSerializer()

    def get_user_instance(self, attr):
        user_data = attr.pop('user')
        return User.objects.create_user(**user_data)

    def get_user_company_qs(self, attr):
        return UserCompany.objects.filter(
            user__email=attr['user']['email'],
            status__in=[
                common_constant.USER_STATUS.ACTIVE,
                common_constant.USER_STATUS.INVITED
            ]
        )

    class Meta(UserCompanySerializer.Meta):
        fields = UserCompanySerializer.Meta.fields + ('user',)


class InviteEmployeeSerializer(UserCompanySerializer):
    '''
    Invite employess to the company.
    '''
    user = InviteUserSerializer()

    def get_user_company_qs(self, attr):
        return UserCompany.objects.filter(
            user__email=attr['user']['email'],
            status__in=[
                common_constant.USER_STATUS.ACTIVE,
                common_constant.USER_STATUS.INVITED
            ]
        )

    def get_company_instance(self, attr):
        user = self.context.get('request').user
        return Company.objects.get(
            user_companies__user=user,
            user_companies__status=common_constant.USER_STATUS.ACTIVE
        )

    def get_user_instance(self, attr):
        user = attr['user']
        try:
            return User.objects.get(email=user['email'])
        except User.DoesNotExist:
            return User.objects.create_user(
                password='DefaultPassword',
                is_active=False,
                **user
            )

    def create(self, validated_data):
        user = self.get_user_instance(validated_data)
        company = self.get_company_instance(validated_data)

        # just a safty precaution
        validated_data.pop('company', None)
        validated_data.pop('user', None)

        instance = UserCompany.objects.create(
            user=user,
            company=company,
            is_admin=False,
            status=common_constant.USER_STATUS.ACTIVE,
            **validated_data
        )
        user.company_create_mail(company.name)
        return instance

    class Meta:
        model = UserCompany
        fields = (
            'user', 'is_admin',
            'designation', 'status'
        )
        extra_kwargs = {

            'designation': {
                'required': True
            },
            'is_admin': {
                'read_only': True
            },
            'status': {
                'read_only': True
            }
        }


class EmployeeSerializer(serializers.ModelSerializer):
    '''
    Employee serializer to fetch company employees
    '''
    user = BaseUserSerializer()

    class Meta:
        model = UserCompany
        fields = ['user', 'designation']
