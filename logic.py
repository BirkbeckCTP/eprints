import requests
import re
from bs4 import BeautifulSoup

from django.utils.text import capfirst
from django.utils import timezone

from submission import models
from journal import models as journal_models


def get_eprints_issues_from_journal(import_obj):
    issue_list = []

    content = requests.get(import_obj.url)
    soup = BeautifulSoup(content.text, "lxml")
    issues = soup.findAll("li", {"class": "journalIssue"})

    for issue in issues:
        issue_list.append({'href': issue.a.get('href'), 'text': issue.a.string})

    return issue_list


def get_eprints_articles_from_journal(url):
    article_list = []

    content = requests.get(url)
    soup = BeautifulSoup(content.text, "lxml")
    forms = soup.findAll("form")

    action = forms[0].get('action')
    request_format = 'JSON'
    view = soup.find("input", {"id": "view"}).get('value')
    values = soup.find("input", {"id": "values"}).get('value')

    url = '{url}?format={format}&view={view}&values={values}'.format(url=action,
                                                                     view=view,
                                                                     format=request_format,
                                                                     values=values)

    json_content = requests.get(url).json()

    for article in json_content:
        article_list.append({'title': article.get('title'), 'url': article.get('official_url')})

    return article_list, url


def import_articles_to_journal(request):
    url = request.POST.get('url')
    import_as_remote = True if 'import_as_remote' in request.POST else False
    json_content = requests.get(url).json()

    for article in json_content:

        section, created = models.Section.objects.language('en').get_or_create(
            journal=request.journal,
            name=capfirst(article.get('type'))
        )

        new_article = models.Article.objects.create(
            journal=request.journal,
            title=article.get('title'),
            owner=request.user,
            abstract=article.get('abstract'),
            is_remote=True,
            remote_url=article.get('official_url'),
            is_import=True if import_as_remote else False,
            section=section,
            stage=models.STAGE_PUBLISHED,
            date_published=article.get('rioxx2_publication_date'),
            peer_reviewed=True if article.get('refereed') == 'TRUE' else False
        )

        issue, created = journal_models.Issue.objects.get_or_create(
            journal=request.journal,
            issue=article.get('number'),
            volume=article.get('volume'),
            issue_type='Issue',
            defaults={'date': timezone.now()}
        )

        issue.articles.add(new_article)


def check_if_issue_exists(issue, request):
    numbers = re.findall(r'\d+', issue.get('text'))

    try:
        issue_obj = journal_models.Issue.objects.get(
            issue=numbers[1],
            volume=numbers[0],
            journal=request.journal)
        return issue_obj
    except journal_models.Issue.DoesNotExist:
        return False
