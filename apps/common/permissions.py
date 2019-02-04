from rest_framework.permissions import IsAuthenticated


class IsNotAuthenticated(IsAuthenticated):
    def has_permission(self, request, view):
        return not super(IsNotAuthenticated, self).has_permission(request, view)
