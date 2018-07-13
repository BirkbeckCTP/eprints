from django.db import models


class Import(models.Model):
    url = models.URLField()
    completed = models.BooleanField(default=False)
    imported_articles = models.ManyToManyField('submission.Article')
