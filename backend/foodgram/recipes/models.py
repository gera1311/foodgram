from django.db import models
from django.contrib.auth import get_user_model


class Tag(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название')
    slug = models.SlugField(max_length=25, verbose_name='Slug')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Ingredient(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=100, verbose_name='Единица измерения')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'


class Recipe(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient',
        related_name='ingredient_recipes',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='Теги')
    cooking_time = models.IntegerField(default=10, blank=True, null=True,
                                       verbose_name='Время приготовления')
    text = models.CharField(max_length=256, blank=True, null=True,
                            verbose_name='Описание')
    image = models.ImageField(blank=True, null=True,
                              verbose_name='Изображение')
    favorites = models.ManyToManyField(
        get_user_model(),
        related_name='favorites_recipe',
        blank=True,
        verbose_name='Подписки'
    )
    author = models.ForeignKey(
        get_user_model(),
        models.CASCADE,
        related_name='author_recipe',
        blank=True,
        null=True,  #Убрать
        verbose_name='Автор'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class Favorite(models.Model):
    'Модель избранного'
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='favorite_recipe_list',
        blank=True,
        null=True
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe_list',
        blank=True,
        null=True
    )


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='recipe_ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   related_name='recipe_ingredients')
    amount = models.CharField(blank=True, null=True, max_length=100)

    class Meta:
        unique_together = ('recipe', 'ingredient')


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='recipe_tags'
    )
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE
    )
