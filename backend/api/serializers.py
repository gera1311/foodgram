from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from django.db import transaction

from recipes.models import Recipe, Tag, Ingredient, RecipeIngredient
from users.models import User, Follow
from .utils import process_ingredients


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Follow.objects.filter(user=user, author=obj).exists()
        return False


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'password')
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('avatar', None)
        return representation


class UserAvatarSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['avatar']


class RecipeImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()

    class Meta:
        model = Recipe
        fields = ['image']


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class IngredientCreateSerializer(IngredientSerializer):

    class Meta(IngredientSerializer.Meta):
        fields = ['name', 'measurement_unit']


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount', ]


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class ShoppingCartSerializer(serializers.ModelSerializer):
    image = Base64ImageField(read_only=True)
    name = serializers.ReadOnlyField()
    cooking_time = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class SubscribeAuthorSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='author_recipes.count',
        read_only=True
    )

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed',
                  'recipes',
                  'recipes_count',
                  'avatar')

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.author_recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = ShoppingCartSerializer(recipes, many=True, read_only=True)
        return serializer.data

    def get_is_subscribed(self, obj):
        # Проверяем, подписан ли текущий пользователь на данного автора
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(user=request.user,
                                         author=obj).exists()
        return False

    def validate(self, obj):
        user = self.context['request'].user
        author = self.instance
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        if (self.context['request'].user == obj):
            raise serializers.ValidationError({'errors': 'Ошибка подписки.'})
        return obj


class AuthorForRecipeSerializer(SubscribeAuthorSerializer):

    class Meta(SubscribeAuthorSerializer.Meta):
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed',
                  'avatar')


class ListRetrieveRecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True,
                                             source='recipe_ingredients')
    tags = TagSerializer(many=True)
    author = AuthorForRecipeSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        ]

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        if user and user.is_authenticated:
            return obj.favorites.filter(id=user.id).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.shopping_recipe.filter(user=user).exists()
        return False


class CreateUpdateDeleteRecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True,
                                             source='recipe_ingredients')
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    image = Base64ImageField()
    author = AuthorForRecipeSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'image',
            'name',
            'text',
            'cooking_time'
        ]
        extra_kwargs = {
            'ingredients': {'required': True},
            'tags': {'required': True},
            'image': {'required': True},
            'name': {'required': True},
            'text': {'required': True},
            'cooking_time': {'required': True}
        }

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        if user and user.is_authenticated:
            return obj.favorites.filter(id=user.id).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        if user and user.is_authenticated:
            return obj.shopping_recipe.filter(id=user.id).exists()
        return False

    def to_representation(self, instance):
        """
        Переопределение метода to_representation для того,
        чтобы вернуть теги с полными данными (например, name и slug).
        """
        representation = super().to_representation(instance)

        tags_ids = representation.get('tags', [])
        tags = Tag.objects.filter(id__in=tags_ids)
        tag_serializer = TagSerializer(tags, many=True)
        representation['tags'] = tag_serializer.data
        return representation

    def validate(self, data):
        # Проверка наличия ингредиентов
        ingredients = data.get('recipe_ingredients', [])
        if self.context['request'].method == 'POST':
            if not ingredients:
                raise serializers.ValidationError(
                    {'ingredients': 'Список ингредиентов пуст.'}
                )
        # Проверка на дублирование ингредиентов
        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться.'}
            )

        # Проверка, что amount каждого ингредиента больше 0
        for ingredient in ingredients:
            if ingredient['amount'] <= 0:
                raise serializers.ValidationError(
                    {'ingredients': 'Количество ингредиента должно быть > 0.'}
                )

        request = self.context['request']
        # Проверка, что изображение передано в запросе
        if request.method == 'POST' and not data.get('image'):
            raise serializers.ValidationError(
                {'image': 'Не указано изображение!'})

        # Проверка наличия тегов
        tags = data.get('tags', [])
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Список тегов не может быть пустым.'}
            )

        # Проверка на дублирование тегов
        tag_ids = [tag.id for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                {'tags': 'Теги не должны повторяться.'}
            )

        return data

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления не может быть меньше 1 минуты.')
        return value

    @transaction.atomic
    def create(self, validated_data):
        # Извлекаем связанные данные
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags_data = validated_data.pop('tags')
        image_data = validated_data.pop('image')

        # Присваиваем автором текущего пользователя
        validated_data['author'] = self.context['request'].user

        # Создаем рецепт
        recipe = Recipe.objects.create(**validated_data)

        # Связываем теги
        recipe.tags.set(tags_data)

        if image_data:
            recipe.image = image_data
            recipe.save()

        process_ingredients(recipe, ingredients_data)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', None)
        tags_data = validated_data.pop('tags', None)

        if tags_data is not None:
            instance.tags.clear()
            instance.tags.set(tags_data)

        # Проверка и обновление изображения
        image = validated_data.get('image', None)
        if image:
            instance.image = image
        else:
            # Если изображение не передано, оставляем старое
            validated_data['image'] = instance.image

        if ingredients_data:
            ingredient_ids = {
                ingredient['id'] for ingredient in ingredients_data}
            instance.recipe_ingredients.exclude(
                ingredient__id__in=ingredient_ids).delete()
            for ingredient_data in ingredients_data:
                ingredient_instance = instance.recipe_ingredients.filter(
                    ingredient__id=ingredient_data['id']).first()
                if ingredient_instance:
                    ingredient_instance.amount = ingredient_data['amount']
                    ingredient_instance.save()
                else:
                    RecipeIngredient.objects.create(
                        recipe=instance, **ingredient_data)
    
        return super().update(instance, validated_data)
