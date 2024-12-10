# Generated by Django 4.2 on 2024-12-09 17:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipes', '0007_alter_recipe_author'),
    ]

    operations = [
        migrations.AlterField(
            model_name='favorite',
            name='recipe',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='favorite_recipe_list', to='recipes.recipe'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='favorite',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='favorite_recipe_list', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='recipe',
            name='author',
            field=models.ForeignKey(blank=True, default=1, on_delete=django.db.models.deletion.CASCADE, related_name='author_recipe', to=settings.AUTH_USER_MODEL, verbose_name='Автор'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='recipe',
            name='cooking_time',
            field=models.IntegerField(default=10, verbose_name='Время приготовления'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='image',
            field=models.ImageField(default=1, upload_to='recipes/images/', verbose_name='Изображение'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='recipe',
            name='text',
            field=models.CharField(default=1, max_length=256, verbose_name='Описание'),
            preserve_default=False,
        ),
    ]
