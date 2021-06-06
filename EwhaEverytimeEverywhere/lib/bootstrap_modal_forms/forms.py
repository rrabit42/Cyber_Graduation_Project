from django import forms

from lib.bootstrap_modal_forms.mixins import PopRequestMixin, CreateUpdateAjaxMixin


class BSModalForm(PopRequestMixin, forms.Form):
    pass


class BSModalModelForm(PopRequestMixin, CreateUpdateAjaxMixin, forms.ModelForm):
    pass
