from rest_framework.permissions import IsAuthenticated

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
