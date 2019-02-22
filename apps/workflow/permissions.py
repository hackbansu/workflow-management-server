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
            return retVal

        return True


class AccessorAccessPermission(company_permissions.IsActiveCompanyEmployee):
    '''
    Check if user is has accessor access permission.
    '''

    def has_permission(self, request, view):
        '''
        Allows admin and workflow write access holders.
        '''
        employee = request.user.active_employee
        # check if workflow exists and is of the same company as the user
        res = super(AccessorAccessPermission, self).has_permission(request, view)
        if not res:
            return False

        workflows = Workflow.objects.filter(pk=view.kwargs['workflow_id'], creator__company=employee.company)
        if not workflows.exists():
            return False

        workflow_instance = workflows[0]
        res = res and (employee.is_admin or workflow_instance.accessors.filter(
            employee=employee,
            permission=common_constant.PERMISSION.READ_WRITE
        ).exists())

        return res
