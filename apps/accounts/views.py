#Django Imports
from django.contrib.auth.views import LoginView,LogoutView, PasswordResetView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View

#Local Application Imports
from .forms import myLoginForm, myPasswordResetForm, myPasswordResetConfirmForm


# UNAUTHENTICATED VIEWS

class myLoginView(LoginView):
    """Override standard login view"""
    form_class = myLoginForm

    def form_valid(self, form):
        response = super(myLoginView, self).form_valid(form)
        return response

class myLogoutView(LogoutView):
    """Override standard logout view - flushes session data"""

    def get(self, request, *args,**kwargs):
        messages.success(request, "You have been successfully logged out")
        self.request.session.flush()
        return redirect('accounts:login')

class myPasswordResetView(PasswordResetView):
    """Override standard password reset form"""
    form_class=myPasswordResetForm
    success_url = reverse_lazy('accounts:password_reset_done')


class myPasswordResetDoneView(View):
    """Override standard password reset done view"""

    def get(self, request):
        messages.success(request, "If you are registered, an email containing reset instructions has been sent")
        return redirect('accounts:login')

class myPasswordResetConfirmView(PasswordResetConfirmView):
    """Override standard password reset confirm form"""
    form_class=myPasswordResetConfirmForm
    success_url = reverse_lazy('accounts:password_reset_complete')


class myPasswordResetCompleteView(PasswordResetCompleteView):
    """Override standard password reset complete view"""

    def get(self,request, *args,**kwargs):
        messages.success(request, "Your password has been set - you may now log in")
        return redirect('accounts:login')



