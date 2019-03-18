import pytz
import re
from urllib.parse import urlsplit

from dateutil import parser
from django.db import transaction
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.conf import settings
import requests

from core import files
from core.models import Account, Galley
from submission.models import Article, Keyword, Licence
from identifiers.models import Identifier
from plugins.eprints.models import ImportedArticleAuthor, ImportedArticleGalley

JSON_EXPORT_TMPL = "{url}/cgi/export/{eprints_id}/JSON/{prefix}-eprint-{eprints_id}"
DOI_RE = re.compile("10.\d{4,9}/[-._;()/:a-zA-Z0-9]+")
DOI_BASE_URL = "http://dx.doi.org/"


def get_eprints_id(url):
    parts = url.split("/")
    eprints_id = parts[-1] or parts[-2] # in case of a trailing slash

    return eprints_id


class Command(BaseCommand):

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('url')
        parser.add_argument('prefix')
        parser.add_argument("--debug", action='store_true', default=False)
        parser.add_argument("--all", action='store_true', default=False,
                help="re-syncs articles that are no longer remote")

    def handle(self, *args, **options):
        debug = options["debug"]
        try:
            return self._handle(*args, **options)
        except Exception as e:
            if debug:
                debug_mode()
            else:
                self.stdout.write(str(e))

    def _handle(self, *args, **options):
        """ Re-syncs article metadata and galley-files from eprints."""

        url = options["url"]
        prefix = options["prefix"]
        sync_all = options["all"]


        remote_articles = Article.objects.filter(remote_url__isnull=False)
        if not sync_all:
            remote_articles = remote_articles.filter(is_remote=True)

        eprints_articles = (
            article for article in remote_articles
            if is_eprints_article(url, article)
        )

        for article in eprints_articles:
            eprints_id = get_eprints_id(article.remote_url)
            self.stdout.write("Re-syncing article %d with eprints ID %s"
                "" % (article.pk, eprints_id)
            )
            try:
                json_url = JSON_EXPORT_TMPL.format(
                    url=url,
                    eprints_id=eprints_id,
                    prefix=prefix,
                )
                response = requests.get(json_url)
                validate_response(response)
                metadata = response.json()
                self.sync_authors(article, metadata)

                self.sync_galleys(article, metadata)
                self.sync_metadata(article, metadata)
                self.sync_doi(article, metadata)
                article.is_remote = False
                article.save()

            except Exception as e:
                self.stderr.write(str(e))
                if options["debug"]:
                    debug_mode()

    def sync_authors(self, article, metadata):
        imported = ImportedArticleAuthor.objects.filter(article=article)

        for author_metadata in metadata["creators"]:
            first_name, middle_name, last_name, email = get_author_details(
                    author_metadata)
            with transaction.atomic():
                author, _ = Account.objects.get_or_create(
                        email=email,
                )
                author.first_name = first_name
                author.last_name = last_name
                author.middle_name = middle_name or None
                author.save()
                # create frozen author record for rendering
                author.snapshot_self(article)

                _, created = ImportedArticleAuthor.objects.get_or_create(
                    article=article,
                    author=author,
                )
                if created:
                    self.stdout.write("Imported author %s" % author)

                if metadata.get("contact_email") == email:
                    article.correspondence_author = author


    def sync_galleys(self, article, metadata):
        """currently only supporting pdf galleys"""
        for document in metadata["documents"]:
            if document["mime_type"] in files.PDF_MIMETYPES:
                file_data = document["files"][0] # PDFs have always one file
                response = requests.get(file_data["uri"], stream=True)
                validate_response(response)
                file_ = SimpleUploadedFile(
                        file_data["filename"],
                        response.content,
                        document["mime_type"],
                )

                if article.pdfs:
                    if len(article.pdfs) > 1:
                        raise RuntimeError("Article has multiple PDF galleys")
                    files.overwrite_file(
                            file_,
                            article.pdfs[0].file,
                            'articles',
                            article.pk,
                    )
                else:
                    saved_file = files.save_file_to_article(file_, article,
                            owner=None,
                            label="pdf",
                            is_galley=True,
                    )
                    galley = Galley.objects.create(
                            article=article,
                            file=saved_file,
                            type="pdf",
                            label="PDF",
                    )
                    article.galley_set.add(galley)

                obj, created = ImportedArticleGalley.objects.get_or_create(
                    article=article,
                    eprint_id=document["eprintid"],
                    version=document["rev_number"],
                    uri=file_data["uri"],
                )
                if created:
                    self.stdout.write("Imported galley: %s " % obj)

    def sync_metadata(self, article, metadata):
        if metadata.get("rioxx2_description"):
            article.abstract = metadata["rioxx2_description"]

        if metadata.get("rioxx2_license_ref"):
            try:
                license_url = metadata["rioxx2_license_ref"].get("license_ref") 
                article.license = Licence.objects.get(
                        journal=article.journal,
                        url=license_url,
                )
            except Licence.DoesNotExist:
                try:
                    split = urlsplit(license_url)
                    split = split._replace(
                        scheme="https" if split.scheme == "http" else "http")
                    article.license = Licence.objects.get(
                            journal=article.journal,
                            url=split.geturl(),
                    )
                except Licence.DoesNotExist:
                    self.stdout.write("Unknown license %s" % license_url)
            article.save()

        if metadata.get("keywords"):
            keywords = metadata["keywords"].split(", ")
            for keyword in keywords:
                obj, created = Keyword.objects.get_or_create(word=keyword)
                article.keywords.add(obj)
        for date in metadata["dates"]:
            if "date_type" not in date:
                article.date_published = parser.parse(str(date["date"])).replace(
                        tzinfo=pytz.UTC)
            elif date["date_type"] == "accepted":
                article.date_accepted = parser.parse(str(date["date"])).replace(
                        tzinfo=pytz.UTC)
            elif date["date_type"] == "published":
                article.date_published = parser.parse(str(date["date"])).replace(
                        tzinfo=pytz.UTC)

    def sync_doi(self, article, metadata):
        try:
            doi_url = metadata["rioxx2_version_of_record"]
            doi_str = re.search(DOI_RE, doi_url).group(0)
        except KeyError:
            self.stdout.write("No DOI record for article in eprints")
            return
        except AttributeError:
            self.stdout.write("Identifier is not a DOI: %s" % doi_url)
            return

        doi, created = Identifier.objects.get_or_create(
            id_type="doi",
            identifier=doi_str,
            article=article,
        )
        if created:
            self.stdout.write("Imported DOI %s " % doi)


def get_author_details(author_metadata):
    given_name = author_metadata["name"]["given"]
    if given_name:
        names = given_name.replace( ".", " ").split( " ", 1)
        first_name = names[0]
        middle_name = " ".join(names[1:])
    else:
        #Corporate authors have "given" set to null
        first_name = middle_name = None
    last_name = author_metadata["name"]["family"]
    email = author_metadata.get("id")
    if email is None:
        domain = settings.DUMMY_EMAIL_DOMAIN
        email = '{}.{}@{}'.format(first_name, last_name, domain)

    return first_name, middle_name, last_name, email

def debug_mode():
    import traceback, pdb, sys
    extype, value, tb = sys.exc_info()
    traceback.print_exc()
    pdb.post_mortem(tb)

def validate_response(response):
    if response.status_code != 200:
        raise RuntimeError(
            "Eprints request failed with code %s",
            response.status_code
        )

def is_eprints_article(eprints_url, article):
    is_eprints = False
    if eprints_url in article.remote_url:
        is_eprints = True
    elif DOI_BASE_URL in article.remote_url:
        req = requests.get(article.remote_url)
        redir = req.history[-1]
        if eprints_url in redir.url:
            article.remote_url = redir.url
            is_eprints = True

    return is_eprints
