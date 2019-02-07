from rest_framework.permissions import IsAuthenticated

from apps.company.models import UserCompany
from apps.common import constant as common_constant


class IsInactiveEmployee(IsAuthenticated):
    '''
    Check if employe is inactive.
    '''

    def has_permission(self, request, view):
        res = super(IsInactiveEmployee, self).has_permission(request, view)
        res = res and not UserCompany.objects.filter(
            user=request.user,
            status__in=[
                common_constant.USER_STATUS.ACTIVE,
                common_constant.USER_STATUS.INVITED
            ]
        ).exists()

        return res


class IsActiveCompanyEmployee(IsAuthenticated):
    '''
    Check if employee is active.
    '''

    def has_permission(self, request, view):
        res = super(IsActiveCompanyEmployee,
                    self).has_permission(request, view)
        return res and request.user.company.status == common_constant.COMPANY_STATUS.ACTIVE


class IsActiveCompanyAdmin(IsAuthenticated):
    '''
    Check if user is company admin.
    '''

    def has_object_permission(self, request, view, obj):
        employee_record = request.user.active_employee
        return employee_record.company == obj.company and employee_record.is_admin
