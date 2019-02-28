from rest_framework.permissions import IsAuthenticated


class IsCompanyAdmin(IsAuthenticated):
    '''
    Check if user is company admin, use for company update.
    '''

    def has_permission(self, request, view):
        employee_record = request.user.active_employee
        return employee_record.is_admin
