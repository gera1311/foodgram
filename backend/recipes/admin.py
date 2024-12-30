from django.contrib import admin

from .models import (
    Recipe, Tag, Ingredient, RecipeIngredient, RecipeTag, Favorite)


class TagAdmin(admin.ModelAdmin):
    search_fields = ['name']
    ordering = ['name']
    verbose_name = 'Тег'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'measurement_unit']
    search_fields = ['name']
    ordering = ['name']
    verbose_name = 'Ингредиент'


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1
    verbose_name = 'Ингредиент в рецепте'
    verbose_name_plural = 'Ингредиенты в рецепте'


class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'ingredient', 'amount']
    search_fields = ['recipe__name', 'ingredient__name']


class RecipeTagInline(admin.TabularInline):
    model = RecipeTag
    verbose_name = 'Тег рецепта'
    verbose_name_plural = 'Теги рецепта'


class TagInRecipeAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'tag']
    search_fields = ['recipe__name', 'tag__name']


class FavoriteAdmin(admin.ModelAdmin):
    model = Favorite


class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline, RecipeTagInline]
    list_display = ['name', 'author', 'favorite_count']
    search_fields = ['name', 'author__username', 'tags__name']

    def favorite_count(self, obj):
        return obj.favorite_recipe.count()
    favorite_count.short_description = 'Число добавлений в избранное'


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(RecipeTag, TagInRecipeAdmin)
admin.site.register(RecipeIngredient, IngredientInRecipeAdmin)
admin.site.register(Favorite, FavoriteAdmin)
