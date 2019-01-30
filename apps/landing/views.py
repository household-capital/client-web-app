from django.contrib.auth.decorators import login_required

from django.views.generic import TemplateView


# Create your views here.

class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **kwargs):
        view = super(LoginRequiredMixin, cls).as_view(**kwargs)
        return login_required(view)

class LandingView(LoginRequiredMixin, TemplateView):

    template_name = "landing/main_landing.html"

    def get_context_data(self, **kwargs):
        context = super(LandingView,self).get_context_data(**kwargs)
        context['page_description']='Please choose an application'
        return context
