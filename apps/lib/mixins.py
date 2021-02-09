from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from apps.enquiry.forms import AddressForm


class AddressLookUpFormMixin(): 
    def get_context_data(self, **kwargs):
        context = super(AddressLookUpFormMixin, self).get_context_data(**kwargs)
        # Pass address form
        context['address_form'] = AddressForm()
        # Ajax URl
        context['ajaxURL'] = reverse_lazy("enquiry:addressComplete")
        return context


class HouseholdLoginRequiredMixin():
    """Ensures views will not render unless logged in, redirects to login page"""
    @classmethod
    def as_view(cls, **kwargs):
        view = super(HouseholdLoginRequiredMixin, cls).as_view(**kwargs)
        return login_required(view)

    # Ensures views will not render unless Household employee, redirects to Landing
    def dispatch(self, request, *args, **kwargs):
        if request.user.profile.isHousehold:
            return super(HouseholdLoginRequiredMixin, self).dispatch(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy('landing:landing'))

class LoginOnlyRequiredMixin():
    """Ensures views will not render unless logged in, redirects to login page"""
    @classmethod
    def as_view(cls, **kwargs):
        view = super(LoginOnlyRequiredMixin, cls).as_view(**kwargs)
        return login_required(view)


class ReferrerLoginRequiredMixin():
    """Ensures views will not render unless logged in, redirects to login page"""
    @classmethod
    def as_view(cls, **kwargs):
        view = super(ReferrerLoginRequiredMixin, cls).as_view(**kwargs)
        return login_required(view)

        # Ensures views will not render unless Household employee, redirects to Landing

    def dispatch(self, request, *args, **kwargs):
        if request.user.profile.referrer:
            return super(ReferrerLoginRequiredMixin, self).dispatch(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy('landing:landing'))
