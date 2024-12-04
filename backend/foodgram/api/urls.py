from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet, IngredientViewSet, TagViewSet, UserViewSet


router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, 'recipe')
router.register(r'tags', TagViewSet, 'tag')
router.register(r'ingredients', IngredientViewSet, 'ingredient')
router.register(r'users', UserViewSet, 'user')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken'))
]