from django.shortcuts import render
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import Recipe, Ingredient, Tag
from users.models import User
from .serializers import ListRetrieveRecipeSerializer, CreateUpdateDeleteRecipeSerializer, IngredientSerializer, TagSerializer, IngredientCreateSerializer, \
                        UserSerializer, UserCreateSerializer, UserAvatarSerializer
from .pagination import CustomPagination
from .utils import decode_base64_image


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ListRetrieveRecipeSerializer
        return CreateUpdateDeleteRecipeSerializer


class IngredientViewSet(mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']


    def get_serializer_class(self):
        if self.action in ['create']:
            return IngredientCreateSerializer
        return IngredientSerializer
    
    http_method_names = ['get']


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class UserViewSet(mixins.CreateModelMixin,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = CustomPagination
    
    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserSerializer
        return UserCreateSerializer
    
    @action(detail=False,
            methods=['get'],
            pagination_class=None,
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = UserSerializer(
            request.user, context=self.get_serializer_context()
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False,
            methods=['put', 'delete'],
            permission_classes=(IsAuthenticated,),
            url_path='me/avatar'
            )
    def change_avatar(self, request):
        if request.method == 'PUT':
            avatar_base64 = request.data.get('avatar')
            if not avatar_base64:
                return Response(
                    {'detail': 'Аватар не найден.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                file_name, content = decode_base64_image(avatar_base64)
                request.user.avatar.save(file_name, content, save=True)
            except ValueError:
                return Response(
                    {'detail': 'Некорректный формат изображения.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = UserAvatarSerializer(
                request.user, context={'request': request}
            )
            return Response(
                serializer.data, status=status.HTTP_200_OK
            )