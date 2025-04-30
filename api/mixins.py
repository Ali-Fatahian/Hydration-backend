from rest_framework.exceptions import PermissionDenied

class IsOwnerMixin:
    """
    Mixin that ensures the object is only accessible by its owner.
    """

    def check_object_permission(self, request, obj):
        # Check if the user is the owner of the object
        if obj.user != request.user:
            raise PermissionDenied("You do not have permission to access this object.")
        return obj
