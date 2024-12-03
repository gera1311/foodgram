from django.contrib import admin

from .models import Recipe, Tag, Ingredient, RecipeIngredient


# class RecipeAdmin(admin.ModelAdmin):
#     list_display = ['name', 'cooking_time', 'text', 'image']

class IngredientAdmin(admin.ModelAdmin):
    search_fields = ['name']  # По какому полю искать в списке ингредиентов


class RecipeIngredientInline(admin.TabularInline):  # Можно использовать StackedInline для более подробного вида
    model = RecipeIngredient
    extra = 1  # Количество пустых форм для добавления по умолчанию
    autocomplete_fields = ['ingredient']  # Автозаполнение для поля ингредиента (если нужно)

class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag)
admin.site.register(Ingredient, IngredientAdmin)
