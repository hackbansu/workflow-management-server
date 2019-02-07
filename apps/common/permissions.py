from rest_framework.permissions import IsAuthenticated


class IsNotAuthenticated(IsAuthenticated):
    '''
    Check if user not authenticated
    '''
    def has_permission(self, request, view):
        return not super(IsNotAuthenticated, self).has_permission(request, view)
