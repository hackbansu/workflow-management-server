from rest_framework.permissions import BasePermission, IsAuthenticated

from apps.company.models import UserCompany
from apps.common import constant as common_constant


class IsInactiveEmployee(IsAuthenticated):
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

class IsActiveEmployee(IsAuthenticated):
    def has_permission(self, request, view):
        res = super(IsActiveEmployee, self).has_permission(request, view)
        res = res and UserCompany.objects.filter(
            user=request.user,
            status=common_constant.USER_STATUS.ACTIVE
        ).exists()
        return res

class IsCompanyAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        res = super(IsCompanyAdmin, self).has_permission(request, view)
        res = res and UserCompany.objects.filter(
            user=request.user,
            status=common_constant.USER_STATUS.ACTIVE,
            is_admin=True
        ).exists()
        return res