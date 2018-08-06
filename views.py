import json
from django.shortcuts import redirect, render, get_object_or_404, HttpResponse
from django.urls import reverse
from django.template.loader import render_to_string

from utils import models as util_models
from plugins.eprints import forms, plugin_settings, models, logic


def index(request):
    """
    Render admin page allowing users to enable or disable the plugin
    """
    plugin = util_models.Plugin.objects.get(name=plugin_settings.SHORT_NAME)
    admin_form = forms.EprintsAdminForm()

    if request.POST:
        admin_form = forms.EprintsAdminForm(request.POST)

        if admin_form.is_valid():
            new_import = models.Import.objects.create(url=admin_form.cleaned_data['eprints_url'])
            new_import.save()

            return redirect(reverse('eprints_import', kwargs={'import_id': new_import.pk}))

    template = "eprints/index.html"
    context = {
        'admin_form': admin_form,
    }

    return render(request, template, context)


def import_journal(request, import_id):
    import_obj = get_object_or_404(models.Import, pk=import_id)

    if request.POST and 'url' in request.POST:
        logic.import_articles_to_journal(request)

    template = 'eprints/import.html'
    context = {
        'import': import_obj,
    }

    return render(request, template, context)


def fetch_eprints_issues(request, import_id):
    import_obj = get_object_or_404(models.Import, pk=import_id)

    issues = logic.get_eprints_issues_from_journal(import_obj)
    for issue in issues:
        issue['exists'] = logic.check_if_issue_exists(issue, request)

    context = {'issues': issues}

    html = render_to_string('eprints/issue_list.html', context)

    return HttpResponse(json.dumps({'status': 200, 'html': html}))


def fetch_eprints_articles(request, import_id):
    get_object_or_404(models.Import, pk=import_id)

    if request.POST:
        url = request.POST.get('url')

        articles, json_url = logic.get_eprints_articles_from_journal(url)

        html = render_to_string('eprints/article_list.html', {'articles': articles, 'url': json_url}, request=request)

        return HttpResponse(json.dumps({'status': 200, 'html': html}))
