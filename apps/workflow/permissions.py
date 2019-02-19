from rest_framework.permissions import IsAuthenticated

from apps.common import constant as common_constant
from apps.company import permissions as company_permissions
from apps.workflow.models import Workflow, WorkflowAccess


class WorkflowAccessPermission(company_permissions.IsActiveCompanyEmployee):
    '''
    Check if user is has workflow access permission.
    '''

    def has_permission(self, request, view):
        '''
        Allows admin to create workflow, admin, accessors and assignees to list and retrieve workflow.
        '''
        res = super(WorkflowAccessPermission, self).has_permission(request, view)

        if view.action == 'create':
            return res and request.user.active_employee.is_admin

        if view.action == 'list':
            return res

        return res

    def has_object_permission(self, request, view, obj):
        employee_record = request.user.active_employee
        if view.action == 'update':
            return employee_record.is_admin or obj.accessors.filter(employee=employee_record, permission=common_constant.PERMISSION.READ_WRITE).exists()

        return True
