from rest_framework.permissions import BasePermission


class IsRecipeAuthor(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Разрешение только автору рецепта
        return obj.author == request.user
