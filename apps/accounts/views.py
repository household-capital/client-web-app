
from django.contrib.auth.views import LoginView,LogoutView, PasswordResetView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View

from .forms import myLoginForm, myPasswordResetForm, myPasswordResetConfirmForm


class myLoginView(LoginView):
    form_class = myLoginForm

    def form_valid(self, form):
        response = super(myLoginView, self).form_valid(form)
        #Session variables Here as required
        return response

class myLogoutView(LogoutView):
    def get(self, request):
        messages.success(request, "You have been successfully logged out")
        self.request.session.flush()
        return redirect('accounts:login')

class myPasswordResetView(PasswordResetView):
    form_class=myPasswordResetForm
    success_url = reverse_lazy('accounts:password_reset_done')

class myPasswordResetDoneView(View):
    def get(self, request):
        messages.success(request, "If you are registered, an email containing reset instructions has been sent")
        return redirect('accounts:login')

class myPasswordResetConfirmView(PasswordResetConfirmView):
    form_class=myPasswordResetConfirmForm
    success_url = reverse_lazy('accounts:password_reset_complete')

class myPasswordResetCompleteView(PasswordResetCompleteView):
    def get(self,request):
        messages.success(request, "Your password has been set - you may now log in")
        return redirect('accounts:login')