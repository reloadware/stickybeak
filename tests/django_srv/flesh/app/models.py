from django.db import models

# Create your models here.


class Currency(models.Model):
    name = models.CharField(max_length=3, unique=True)
    endpoint = models.URLField(max_length=256)

    def __str__(self):
        return str(self.code)
