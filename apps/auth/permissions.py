from rest_framework.permissions import IsAuthenticated
from apps.common import constant as common_constant

from apps.company.models import Company, UserCompany


class IsSelfOrCompanyAdmin(IsAuthenticated):
    '''
    Check if the data is edited by self or the company admin only.
    '''

    def has_object_permission(self, request, view, obj):
        '''
        Check for user in self of admin in same company. 
        '''
        try:
            company = obj.user_companies.get(
                status=common_constant.USER_STATUS.ACTIVE).company
            request.user.user_companies.get(
                company=company,
                is_admin=True,
                status=common_constant.USER_STATUS.ACTIVE
            )
        except (Company.DoesNotExist, UserCompany.DoesNotExist):
            return False
        return request.user == obj
