from django.contrib import admin

from .models import Recipe, Tag, Ingredient, RecipeIngredient


class IngredientAdmin(admin.ModelAdmin):
    search_fields = ['name']


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ['ingredient']


class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag)
admin.site.register(Ingredient, IngredientAdmin)
