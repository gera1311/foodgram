from rest_framework import serializers

from recipes.models import Recipe, Tag, Ingredient, RecipeIngredient
from users.models import User, Follow
from .utils import decode_base64_image


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
        fields = ['avatar',]


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
    """Сериализатор для связи рецепт-ингредиент с количеством."""
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


class ListRetrieveRecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True,
                                             source='recipe_ingredients')
    tags = TagSerializer(many=True)

    class Meta:
        model = Recipe
        fields = '__all__'


class CreateUpdateDeleteRecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True,
                                             source='recipe_ingredients')
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    image = serializers.CharField(required=False)

    class Meta:
        model = Recipe
        fields = [
            'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time'
        ]
        extra_kwargs = {
            'ingredients': {'required': True},
            'tags': {'required': True},
            'image': {'required': True},
            'name': {'required': True},
            'text': {'required': True},
            'cooking_time': {'required': True}
        }

    def to_representation(self, instance):
        """
        Переопределение метода to_representation для того,
        чтобы вернуть теги с полными данными (например, name и slug)
        """
        representation = super().to_representation(instance)

        # Получаем ID тегов
        tags_ids = representation.get('tags', [])

        # Извлекаем объекты тегов по их ID
        tags = Tag.objects.filter(id__in=tags_ids)

        # Сериализуем теги
        tag_serializer = TagSerializer(tags, many=True)

        # Заменяем ID тегов на полные данные
        representation['tags'] = tag_serializer.data

        return representation

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления не может быть меньше 1 минуты.')
        return value

    def create(self, validated_data):
        # Извлекаем связанные данные
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags_data = validated_data.pop('tags')

        # Если в данных есть изображение, декодируем его
        image_data = validated_data.pop('imgae', None)
        if image_data:
            file_name, content_file = decode_base64_image(image_data)
            validated_data['image'] = content_file

        recipe = Recipe.objects.create(**validated_data)

        # Связываем теги
        recipe.tags.set(tags_data)

        # Добавляем ингредиенты
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
            )

        return recipe

    def update(self, instance, validated_data):
        # Удаляем старые связи и пересоздаем их
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags_data = validated_data.pop('tags')

        instance.tags.clear()
        instance.tags.set(tags_data)

        RecipeIngredient.objects.filter(recipe=instance).delete()

        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
            )

        return super().update(instance, validated_data)


class SubscribeAuthorSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'avatar', 'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        # Получаем список рецептов автора
        recipes = obj.author_recipe.all()  # Предполагаем, что related_name = 'author_recipe'
        return [
            {
                "id": recipe.id,
                "name": recipe.name,
                "image": recipe.image.url if recipe.image else None,
                "cooking_time": recipe.cooking_time
            }
            for recipe in recipes
        ]

    def get_recipes_count(self, obj):
        # Подсчитываем количество рецептов автора
        return obj.author_recipe.count()

    def get_is_subscribed(self, obj):
        # Проверяем, подписан ли текущий пользователь на данного автора
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(user=request.user, author=obj).exists()
        return False

    def validate(self, data):
        """Валидация, чтобы предотвратить повторную подписку на автора."""
        user = self.context['request'].user
        author = self.instance  # объект User, на которого происходит подписка
        if Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError("Вы уже подписаны на этого автора.")
        if user == author:
            raise serializers.ValidationError("Нельзя подписаться на самого себя.")
        return data
