import json
import requests
from bs4 import BeautifulSoup


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

    return article_list

