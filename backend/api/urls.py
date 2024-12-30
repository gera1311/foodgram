from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet, IngredientViewSet, TagViewSet, UserViewSet


router = DefaultRouter()
router.register('recipes', RecipeViewSet, 'recipe')
router.register('tags', TagViewSet, 'tag')
router.register('ingredients', IngredientViewSet, 'ingredient')
router.register('users', UserViewSet, 'user')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
