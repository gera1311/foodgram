from django.contrib import admin

from .models import ShoppingCart


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'user']


admin.site.register(ShoppingCart, ShoppingCartAdmin)
