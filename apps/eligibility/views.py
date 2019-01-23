
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.contrib import messages

from django.views.generic import FormView, TemplateView, View


from .forms import ValidateForm, EmailForm
from apps.utilities import chkCreditCriteria


# Create your views here.

class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **kwargs):
        view = super(LoginRequiredMixin, cls).as_view(**kwargs)
        return login_required(view)

class LandingView(LoginRequiredMixin, FormView):

    template_name = "eligibility/main_eligibility.html"
    form_class=ValidateForm
    success_url = reverse_lazy('eligibility:landing')

    def get_context_data(self, **kwargs):
        context = super(LandingView,self).get_context_data(**kwargs)
        context['title'] = 'Calculate Eligibility'
        context['title_icon'] = 'fas fa-search'
        context['page_description']='Enter borrower and property details to check eligibility'
        return context

    def form_valid(self, form):
        #Override redirect
        context=self.get_context_data(form=form)

        #remove validationDictionary from the session if already exists
        if 'validationDict' in self.request.session.items():
            self.request.session.pop('validationDict')

        if form.cleaned_data['borrower_type']=='SINGLE':
            isJoint=False
        else:
            isJoint=True

        if form.cleaned_data['dwelling_type'] == 'HOUSE':
            isApartment = False
        else:
            isApartment = True

        validationDict=chkCreditCriteria(isJoint,
                                         int(form.cleaned_data['youngest_age']),
                                         isApartment,
                                         form.cleaned_data['postcode'],
                                         float(form.cleaned_data['valuation'].replace(',',''))
                                         )

        context.update(validationDict)

        if validationDict['eligible']==True:
            self.request.session['validationDict']=validationDict
            for key, value in self.request.session.items():
                print('{} => {}'.format(key, value))

        return self.render_to_response(context)


class EmailView(LoginRequiredMixin, FormView):

    template_name = "eligibility/main_eligibility.html"
    form_class=EmailForm
    success_url = reverse_lazy('eligibility:landing')

    def get_context_data(self, **kwargs):
        context = super(EmailView,self).get_context_data(**kwargs)
        context['title'] = 'Draft Email'
        context['title_icon'] = 'far fa-envelope'
        context['page_description']='Enter additional details to create a draft adviser email '

        return context

    def form_valid(self,form):

        template_html = "eligibility/email.html"
        email_context = self.request.session['validationDict']
        for key, value in form.cleaned_data.items():
            email_context[key]=value

        subject, from_email, to = "Household Loan Enquiry - "+email_context['client_reference'], \
                                  settings.DEFAULT_FROM_EMAIL, \
                                  self.request.user.email
        text_content = "Text Message"

        html = get_template(template_html)
        html_content = html.render(email_context)
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        messages.success(self.request, "Draft has been emailed to you")

        return super(EmailView,self).form_valid(form)


