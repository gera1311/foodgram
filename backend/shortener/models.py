from django.db import models


class ShortLink(models.Model):
    short_code = models.CharField(max_length=10, unique=True)
    original_url = models.URLField()

    def __str__(self):
        return f'{self.short_code} -> {self.original_url}'
