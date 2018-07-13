from django import forms


class EprintsAdminForm(forms.Form):
    eprints_url = forms.CharField(required=True)
