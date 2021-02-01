
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, CreateView, TemplateView, View, FormView, DetailView
from django.contrib import messages

from apps.lib.site_Utilities import HouseholdLoginRequiredMixin

from .models import GlobalSettings
from .forms import GlobalSettingsForm


class GlobalSettingView(HouseholdLoginRequiredMixin, UpdateView):

    # List view of all loans (Facility Objects)
    template_name = 'settings/global.html'
    form_class = GlobalSettingsForm
    model = GlobalSettings

    def get_context_data(self, **kwargs):
        context = super(GlobalSettingView, self).get_context_data(**kwargs)
        return context

    def get_object(self, queryset=None):
        return GlobalSettings.load()

    def form_valid(self, form):
        obj = form.save(commit=True)
        messages.success(self.request, "Settings Saved")

        return HttpResponseRedirect(reverse_lazy('settings:globalSettings'))
