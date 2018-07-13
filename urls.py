from django.conf.urls import url
from plugins.eprints import views

urlpatterns = [
    url(r'^$', views.index, name='eprints_index'),
    url(r'^import/(?P<import_id>\d+)/$', views.import_journal, name='eprints_import'),
    url(r'^import/(?P<import_id>\d+)/issue_list$', views.fetch_eprints_issues, name='eprints_fetch_issues'),
    url(r'^import/(?P<import_id>\d+)/fetch_articles', views.fetch_eprints_articles, name='eprints_fetch_articles'),
    # declare further URLS here   
]
