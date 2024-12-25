import pyshorteners

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins, status, serializers, filters
from rest_framework.response import Response
from rest_framework.permissions import (IsAuthenticated,
                                        AllowAny,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.decorators import action
from djoser.serializers import SetPasswordSerializer as \
    DjoserSetPasswordSerializer
from django_filters.rest_framework import DjangoFilterBackend

from .filters import RecipeFilter
from recipes.models import Recipe, Ingredient, Tag, RecipeIngredient
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
                          SubscribeAuthorSerializer)
from .pagination import CustomPagination
from .permissions import IsRecipeAuthor
from .utils import decode_base64_image, ShoppingCartFileGenerator


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
        try:
            # Получаем рецепт
            recipe = self.get_object()

            # Формируем полный URL рецепта
            full_url = request.build_absolute_uri(f'/api/recipes/{recipe.id}/')

            # Генерируем короткую ссылку
            shortener = pyshorteners.Shortener()
            short_url = shortener.tinyurl.short(full_url)

            short_link = short_url.replace('tinyurl.com',
                                           'foodgram.example.org/s')

            # Возвращаем короткую ссылку
            return Response({'short-link': short_link},
                            status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'Не удалось создать короткую ссылку: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

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
            data = {
                "id": recipe.id,
                "name": recipe.name,
                "image": request.build_absolute_uri(
                    recipe.image.url) if recipe.image else None,
                "cooking_time": recipe.cooking_time
            }
            return Response(data, status=status.HTTP_201_CREATED)

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
    def add_to_shopping_cart(self, request, pk=None):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(
                {'error': 'Рецепт не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Сериализуем рецепт
        serializer = ShoppingCartSerializer(recipe,
                                            context={'request': request})

        if request.method == 'POST':
            # Добавляем рецепт в корзину
            try:
                serializer.add_to_cart(request.user)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            except serializers.ValidationError as e:
                return Response({'error': e},
                                status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            # Удаляем рецепт из корзины
            try:
                serializer.remove_from_cart(request.user)
                return Response(status=status.HTTP_204_NO_CONTENT)
            except serializers.ValidationError as e:
                return Response({'error': e},
                                status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        shopping_cart = ShoppingCart.objects.filter(user=request.user)
        if not shopping_cart.exists():
            return Response(
                {'error': 'Корзина покупок пуста.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Подсчитываем ингредиенты
        ingredients = {}
        for item in shopping_cart:
            recipe = item.recipe
            for recipe_ingredient in RecipeIngredient.objects.filter(
                    recipe=recipe):
                ingredient = recipe_ingredient.ingredient
                if ingredient.name in ingredients:
                    ingredients[ingredient.name]['amount'] += (
                        recipe_ingredient.amount)
                else:
                    ingredients[ingredient.name] = {
                        'amount': recipe_ingredient.amount,
                        'unit': ingredient.measurement_unit,
                    }

        # Генерация файла
        file_format = request.query_params.get('format', 'txt')
        file_generator = ShoppingCartFileGenerator()
        if file_format == 'txt':
            return file_generator.generate_txt(ingredients)
        elif file_format == 'pdf':
            return file_generator.generate_pdf(ingredients)
        elif file_format == 'csv':
            return file_generator.generate_csv(ingredients)
        else:
            return Response(
                {'error': 'Укажите формат файла (txt, pdf, csv) в запросе.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class IngredientViewSet(mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            return queryset.filter(name__icontains=name)
        return queryset

    def get_serializer_class(self):
        if self.action in ['create']:
            return IngredientCreateSerializer
        return IngredientSerializer

    http_method_names = ['get']


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
        print("Request data:", request.data)
        serializer = DjoserSetPasswordSerializer(
            instance=request.user,
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid(raise_exception=True):
            print("Password valid:", serializer.validated_data)
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
                author, context={'request': request})
            serializer.validate({})
            Follow.objects.create(user=request.user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

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
