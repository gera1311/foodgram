from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins, status, filters
from rest_framework.response import Response
from rest_framework.permissions import (IsAuthenticated,
                                        AllowAny,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.decorators import action
from djoser.serializers import (
    SetPasswordSerializer as DjoserSetPasswordSerializer)
from django_filters.rest_framework import DjangoFilterBackend

from .filters import RecipeFilter, IngredientFilter
from recipes.models import Recipe, Ingredient, Tag
from users.models import User, Follow
from carts.models import ShoppingCart
from .serializers import (ListRetrieveRecipeSerializer,
                          CreateUpdateDeleteRecipeSerializer,
                          ShoppingCartSerializer,
                          IngredientSerializer,
                          TagSerializer,
                          IngredientCreateSerializer,
                          UserSerializer,
                          UserCreateSerializer,
                          SubscribeAuthorSerializer,
                          FavoriteSerializer)
from .pagination import CustomPagination
from .permissions import IsRecipeAuthor
from .utils import (
    decode_base64_image,
    generate_shopping_cart_report,
    handle_add_remove_action)
from shortener.views import create_short_link


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    permission_classes = (IsAuthenticatedOrReadOnly, IsRecipeAuthor,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ListRetrieveRecipeSerializer
        return CreateUpdateDeleteRecipeSerializer

    def get_permissions(self):
        # Разрешаем всем доступ на чтение, только автору — редактирование
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsRecipeAuthor]
        else:
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return super().get_permissions()

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        full_url = request.build_absolute_uri(f'/api/recipes/{recipe.id}/')
        short_link = create_short_link(full_url)
        short_url = request.build_absolute_uri(f'/s/{short_link.short_code}/')
        return Response({'short-link': short_url}, status=status.HTTP_200_OK)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])
        user = request.user

        if request.method == 'POST':
            if recipe.favorites.filter(id=user.id).exists():
                return Response({'detail': 'Рецепт уже в избранном.'},
                                status=status.HTTP_400_BAD_REQUEST)
            recipe.favorites.add(user)
            serializer = FavoriteSerializer(recipe,
                                            context={'request': request})

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not recipe.favorites.filter(id=user.id).exists():
                return Response({'detail': 'Рецепта нет в избранном.'},
                                status=status.HTTP_400_BAD_REQUEST)
            recipe.favorites.remove(user)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def add_to_shopping_cart(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = ShoppingCartSerializer(
                recipe, data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            data = {'user': request.user, 'recipe': recipe}
            return handle_add_remove_action(
                model=ShoppingCart, data=data,
                error_message='Рецепт уже в списке покупок.',
                success_message=serializer.data
            )

        if request.method == 'DELETE':
            shopping_cart_item = ShoppingCart.objects.filter(
                user=request.user, recipe=recipe).first()
            if shopping_cart_item:
                shopping_cart_item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': 'Этот рецепт не найден в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        file_format = request.query_params.get('format', 'txt')
        file_data, error = generate_shopping_cart_report(request.user,
                                                         file_format)

        if error:
            return Response(
                {'error': error},
                status=status.HTTP_400_BAD_REQUEST
            )

        return file_data


class IngredientViewSet(mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']
    filterset_class = IngredientFilter
    http_method_names = ['get']

    def get_serializer_class(self):
        if self.action in ['create']:
            return IngredientCreateSerializer
        return IngredientSerializer


class TagViewSet(mixins.RetrieveModelMixin,
                 mixins.ListModelMixin,
                 viewsets.GenericViewSet):
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
            methods=['post'],
            permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        serializer = DjoserSetPasswordSerializer(
            instance=request.user,
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid(raise_exception=True):
            request.user.set_password(
                serializer.validated_data['new_password'])
            request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

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
                relative_path, content = decode_base64_image(
                    avatar_base64,
                    folder_name='avatars')
                request.user.avatar.save(relative_path, content, save=True)
            except ValueError:
                return Response(
                    {'detail': 'Некорректный формат изображения.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Возвращаем ссылку на новый аватар
            return Response({'avatar': request.user.avatar.url},
                            status=status.HTTP_200_OK)

        elif request.method == 'DELETE':
            if request.user.avatar:
                request.user.avatar.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            return Response(
                {'detail': 'У пользователя нет аватара.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = SubscribeAuthorSerializer(
                author, data=request.data, context={'request': request})
            if not serializer.is_valid(raise_exception=True):
                return Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
            data = {'user': request.user, 'author': author}
            return handle_add_remove_action(
                model=Follow,
                data=data,
                error_message='Вы уже подписаны на этого автора.',
                success_message=serializer.data,
            )

        elif request.method == 'DELETE':
            subscription = Follow.objects.filter(
                user=request.user, author=author).first()
            if subscription:
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'detail': 'Вы не подписаны на этого автора'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,),
            pagination_class=CustomPagination)
    def subscriptions(self, request):
        queryset = User.objects.filter(follower__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscribeAuthorSerializer(page,
                                               many=True,
                                               context={'request': request})
        return self.get_paginated_response(serializer.data)
