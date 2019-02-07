from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from rest_framework import serializers

from apps.auth.serializers import CreateUserSerializer, InviteUserSerializer
from apps.common import constant as common_constant
from apps.company.models import Company, Link, UserCompany

User = get_user_model()


class LinkSerializer(serializers.ModelSerializer):
    '''
    Company link serializer.
    '''
    class Meta:
        model = Link
        fields = ('link_type', 'url')


class CompanySerializer(serializers.ModelSerializer):
    '''
    Company model serializer.
    '''
    status = serializers.SerializerMethodField()
    links = LinkSerializer(many=True)

    def get_status(self, obj):
        '''
        return status equivalent.
        '''
        return obj.get_status_display()

    def validate_name(self, value):
        '''
        validate for company name.
        '''
        qs = Company.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance)
        if qs.exists():
            raise serializers.ValidationError(
                {
                    'detail': 'This company name is already taken.'
                }
            )
        return value

    def create(self, validated_data):
        '''
        update due to nested write.
        '''
        links_data = validated_data.pop('links', None)
        company = super(CompanySerializer, self).create(self, validated_data)
        if links_data:
            for link in links_data:
                Link.objects.create(company=company, **link)
        return company

    def update(self, instance, validated_data):
        '''
        override due to nested write.
        '''
        links_data = validated_data.pop('links', None)

        if links_data:
            for link in links_data:
                try:
                    link_instance = Link.objects.get(
                        company=instance,
                        link_type=link['link_type'],
                    )
                    link_instance.url = link['url']
                    link_instance.save()
                except Link.DoesNotExist:
                    Link.objects.create(company=instance, **link)

        return super(CompanySerializer, self).update(instance, validated_data)

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
            'status': {
                'read_only': True
            },
            'name': {
                'read_only': True
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
        '''
        return user instance, can be override to adapt to get user from diffent. 
        '''
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
            status=common_constant.USER_STATUS.INVITED,
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
    user = CreateUserSerializer()

    def get_user_instance(self, attr):
        user_data = attr.pop('user')
        user = User.objects.create_user(
            is_active=False,
            password='DefaultPassword',
            **user_data
        )
        user.verification_mail()
        return user

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
    user = CreateUserSerializer()

    def update(self, instance, validated_data):
        '''
        override because of nested write
        '''
        user_data = validated_data.pop('user', None)
        if user_data:
            # just a precaution
            user_data.pop('email', None)
            user = instance.user
            for attr, value in user_data.items():
                try:
                    user._meta.get_field(attr)
                    setattr(user, attr, value)
                except FieldDoesNotExist:
                    pass
            user.save()

        return super(EmployeeSerializer, self).update(instance, validated_data)

    class Meta:
        model = UserCompany
        fields = ['user', 'designation', 'is_admin', 'status', 'id']
    
        


class EmployeeCompanySerializer(serializers.ModelSerializer):
    '''
    Employee company and company related details. 
    '''
    company = CompanySerializer()

    def update(self, instance, validated_data):
        '''
        override for nested updates
        '''
        company_data = validated_data.pop('company', None)
        if company_data:
            company_serializer = CompanySerializer(
                data=company_data,
                instance=instance.company
            )
            company_serializer.is_valid(raise_exception=True)
            company_serializer.save()
        return super(EmployeeCompanySerializer, self).update(instance, validated_data)

    class Meta:
        model = UserCompany
        fields = ('company', 'designation', 'is_admin', 'status', 'id')
        extra_kwargs = {
            'id': {
                'read_only': True
            },
            'status': {
                'read_only': True
            }
        }
