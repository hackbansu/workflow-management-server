from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q
from django.utils import timezone

from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from apps.auth.serializers import UpdateUserSerializer, CreateUserSerializer, InviteUserSerializer, BaseUserSerializer
from apps.common import constant as common_constant
from apps.company.models import Company, Link, UserCompany, UserCompanyCsv
from apps.auth.serializers import ResetPasswordSerializer

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
    links = LinkSerializer(many=True, required=False)
    logo_url = serializers.URLField(source='logo', read_only=True)

    class Meta:
        model = Company
        fields = ('id', 'name', 'address', 'city', 'state',
                  'logo', 'logo_url', 'status', 'links')
        extra_kwargs = {
            'id': {
                'read_only': True,
                'help_text': 'unique company id'
            },
            'logo': {
                'write_only': True,
                'help_text': 'company logo'
            },
            'status': {
                'read_only': True
            },

        }

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

        # just a precaution
        validated_data.pop('name', None)

        return super(CompanySerializer, self).update(instance, validated_data)


class UserCompanySerializer(serializers.ModelSerializer):
    '''
    Create company with existing user.
    '''
    company = CompanySerializer()

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

    def get_user_instance(self, attr):
        '''
        return user instance, can be override to adapt to get user from diffrent.
        '''
        user = self.context.get('request').user
        return user

    def get_user_company_qs(self, attr):
        user = self.get_user_instance(attr)
        return UserCompany.objects.filter(
            Q(user=user.id) &
            (
                Q(status=common_constant.USER_STATUS.ACTIVE) |
                Q(is_admin=True)
            )
        )

    def get_company_instance(self, attr):
        company = Company.objects.create(**attr.pop('company'))
        return company

    def validate(self, validated_data):
        qs = self.get_user_company_qs(validated_data)

        if qs.exists():
            raise serializers.ValidationError(
                {'detail': 'User already part of a company'})
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
        company.create_mail()
        instance.send_invite()
        return instance


class UserCompanyCsvSerializer(serializers.ModelSerializer):
    '''
    Company link serializer.
    '''

    status = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = UserCompanyCsv
        fields = ('csv_file', 'status')
        extra_kwargs = {
            'csv_file': {
                'write_only': True
            }
        }

    def create(self, validated_data):
        user_company = self.context['request'].user.active_employee
        # just a safty precaution
        validated_data.pop('user_company', None)

        instance = UserCompanyCsv.objects.create(
            user_company=user_company,
            **validated_data
        )
        return instance


class UserCompanySignupSerializer(UserCompanySerializer):
    '''
    User Company serializer for simultaneous signup.
    '''
    user = CreateUserSerializer()

    class Meta(UserCompanySerializer.Meta):
        fields = UserCompanySerializer.Meta.fields + ('user',)

    def get_user_instance(self, attr):
        user_data = attr.pop('user')
        user = User.objects.create_user(
            is_active=False,
            password='DefaultPassword',
            **user_data
        )
        return user

    def get_user_company_qs(self, attr):
        return UserCompany.objects.filter(
            Q(user__email=attr['user']['email']) &
            (
                Q(status=common_constant.USER_STATUS.ACTIVE) |
                Q(is_admin=True)
            )
        )


class InviteEmployeeSerializer(UserCompanySerializer):
    '''
    Invite employess to the company.
    '''
    user = InviteUserSerializer()

    class Meta:
        model = UserCompany
        fields = ('user', 'is_admin', 'designation', 'status')
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

    def get_user_company_qs(self, attr):
        company = self.get_company_instance(attr)
        return UserCompany.objects.filter(
            Q(user__email=attr['user']['email'],) &
            Q(status=common_constant.USER_STATUS.ACTIVE)
        )

    def get_company_instance(self, attr):
        if hasattr(self, 'company'):
            return self.company
        user = self.context.get('request').user
        self.company = user.company
        return self.company

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

        instance, _ = UserCompany.objects.get_or_create(
            user=user,
            company=company,
            status=common_constant.USER_STATUS.INVITED,
            defaults=validated_data
        )

        instance.send_invite()
        return instance


class InviteEmployeeCsvSerializer(InviteEmployeeSerializer):
    '''
    Invite employess to the company via csv.
    '''
    class Meta(InviteEmployeeSerializer.Meta):
        pass

    def get_company_instance(self, attr):
        if hasattr(self, 'company'):
            return self.company
        user = self.context.get('user')
        self.company = user.company
        return self.company


class InvitationSerializer(ResetPasswordSerializer):
    '''
    Serializer to accept invitaion of user
    '''

    def update(self, instance, validated_data):
        '''
        Override to activate employee account.
        '''
        user_company = self.context['user_company']
        user_company.status = common_constant.USER_STATUS.ACTIVE
        user_company.join_at = timezone.now()
        user_company.save()

        qs = self.instance.user_companies.filter(
            status=common_constant.USER_STATUS.INVITED
        )
        if qs.exists():
            qs.delete()

        return super(InvitationSerializer, self).update(instance, validated_data)


class EmployeeAdminSerializer(serializers.ModelSerializer):
    '''
    Employee serializer to fetch company employees
    '''
    user = UpdateUserSerializer()

    class Meta:
        model = UserCompany
        fields = ('user', 'designation', 'is_admin',
                  'status', 'id', 'join_at', 'left_at')
        read_only_fields = ('join_at', 'left_at')

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

        return super(EmployeeAdminSerializer, self).update(instance, validated_data)


class EmployeeCompanySerializer(serializers.ModelSerializer):
    '''
    Employee's company and company related details.
    '''
    company = CompanySerializer()

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


class EmployeesSerializer(serializers.ModelSerializer):
    user = BaseUserSerializer()

    class Meta:
        model = UserCompany
        fields = ('user', 'designation', 'is_admin', 'id')
        read_only_fields = ('user', 'designation', 'is_admin', 'id')
