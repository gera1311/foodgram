from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer as \
    DjoserSetPasswordSerializer

from recipes.models import Recipe, Ingredient, Tag
from users.models import User
from .serializers import (ListRetrieveRecipeSerializer,
                          CreateUpdateDeleteRecipeSerializer,
                          IngredientSerializer,
                          TagSerializer,
                          IngredientCreateSerializer,
                          UserSerializer,
                          UserCreateSerializer, UserAvatarSerializer)
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
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']

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

        elif request.method == 'DELETE':
            if request.user.avatar:
                request.user.avatar.delete()
                request.user.avatar = None
                request.user.save()
                return Response(
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {'detail': 'У пользователя нет аватара.'},
                status=status.HTTP_400_BAD_REQUEST
            )
