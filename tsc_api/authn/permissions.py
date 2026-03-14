from rest_framework.permissions import SAFE_METHODS, BasePermission


class RoleAccessPermission(BasePermission):
    catalog_view_names = {'countries', 'systems', 'findings'}

    def has_permission(self, request, view):
        user = request.user
        role = getattr(getattr(user, 'role', None), 'role_name', '')
        role = (role or '').upper()

        if role == 'ADMIN':
            return True

        if role == 'EDITOR':
            if getattr(view, 'basename', None) in self.catalog_view_names:
                return request.method in SAFE_METHODS
            return True

        if role == 'VIEWER':
            return request.method in SAFE_METHODS

        return False
