from django.contrib import admin

from .models import ShoppingCart


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'user', 'quantity']


admin.site.register(ShoppingCart, ShoppingCartAdmin)
