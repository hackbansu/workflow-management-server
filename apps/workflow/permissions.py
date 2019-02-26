from rest_framework.permissions import IsAuthenticated, SAFE_METHODS

from apps.common import constant as common_constant
from apps.company import permissions as company_permissions
from apps.workflow.models import Workflow, WorkflowAccess


class hasWorkflowWritePermission(IsAuthenticated):
    '''
    Checks if user has write permissions to the given workflow.
    '''

    def has_object_permission(self, request, view, obj):
        '''
        Checks if user has write permissions of the given workflow.

        Arguments:
            company_permissions {[type]} -- [description]
            request {object} -- request object
            obj {object} -- workflow object

        Returns:
            boolean -- has access or not
        '''

        employee_record = request.user.active_employee
        # check if workflow belongs to the same company as of the user
        if not obj.creator.company == employee_record.company:
            return False

        retVal = employee_record.is_admin
        retVal = retVal or obj.accessors.filter(employee=employee_record,
                                                permission=common_constant.PERMISSION.READ_WRITE).exists()
        return retVal


class WorkflowAccessPermission(company_permissions.IsActiveCompanyEmployee, hasWorkflowWritePermission):
    '''
    Check if user is has workflow access permission.
    '''

    def has_permission(self, request, view):
        '''
        Allows admin to create workflow, admin, accessors and assignees to list and retrieve workflow.
        '''
        res = super(WorkflowAccessPermission, self).has_permission(request, view)

        if request.method == 'POST':
            return res and request.user.active_employee.is_admin

        return res

    def has_object_permission(self, request, view, obj):
        employee_record = request.user.active_employee
        if request.method not in SAFE_METHODS:
            return super(WorkflowAccessPermission, self).has_object_permission(request, view, obj)

        return True


class TaskAccessPermission(company_permissions.IsActiveCompanyEmployee, hasWorkflowWritePermission):
    '''
    Check if user is has task access permission.
    '''

    def has_permission(self, request, view):
        '''
        Allows company employees to view their tasks.
        '''
        res = super(TaskAccessPermission, self).has_permission(request, view)
        return res

    def has_object_permission(self, request, view, obj):
        employee_record = request.user.active_employee

        if request.method not in SAFE_METHODS:
            retVal = super(TaskAccessPermission, self).has_object_permission(request, view, obj.workflow)
            retVal = obj.assignee == employee_record or retVal

            if request.method == 'PUT' or request.method == 'PATCH':
                retVal = retVal and not obj.status == common_constant.TASK_STATUS.COMPLETE

            return retVal

        return True
