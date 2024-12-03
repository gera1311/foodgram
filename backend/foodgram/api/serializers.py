from rest_framework import serializers

from recipes.models import Recipe, Tag, Ingredient, RecipeIngredient, RecipeTag
from users.models import User, Follow


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
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount', ]


class ListRetrieveRecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True, source='recipe_ingredients')
    tags = TagSerializer(many=True)

    class Meta:
        model = Recipe
        fields = '__all__'


class CreateUpdateDeleteRecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True, source='recipe_ingredients')
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)

    class Meta:
        model = Recipe
        fields = ['ingredients', 'tags', 'image', 'name', 'text', 'cooking_time']

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
            raise serializers.ValidationError('Время приготовления не может быть меньше 1 минуты.')
        return value
    
    def create(self, validated_data):
        # Извлекаем связанные данные
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags_data = validated_data.pop('tags')
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


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'avatar')
    
    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Follow.objects.filter(user=user, author=obj).exists()
        return False


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = '__all__'


class UserAvatarSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['avatar',]
