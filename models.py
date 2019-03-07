from django.db import models


class Import(models.Model):
    url = models.URLField()
    completed = models.BooleanField(default=False)
    imported_articles = models.ManyToManyField('submission.Article')

class ImportedArticleAuthor(models.Model):
    article = models.ForeignKey("submission.Article")
    author = models.ForeignKey("core.Account")

    class Meta:
        unique_together = (("article", "author"),)

class ImportedArticleGalley(models.Model):
    article = models.ForeignKey("submission.Article")
    eprint_id = models.PositiveIntegerField()
    version = models.PositiveIntegerField()
    uri = models.URLField()

    def __str__(self):
        return "{}({}, eprint_id={}, version={}, uri={})".format(
                self.__class__.__name__,
                self.article,
                self.eprint_id,
                self.version,
                self.uri,
        )

