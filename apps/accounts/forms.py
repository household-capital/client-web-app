#Django Imports
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm

#Third-party Imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div



class myLoginForm(AuthenticationForm):
    """Override login form using Crispy form"""
    def __init__(self,*args, **kwargs):
        super(myLoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.field_class='col-11'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_show_labels = False
        self.helper.form_show_errors=False
        self.helper.layout = Layout(Div(Field('username', placeholder='username'), css_class="form-group"),
                                    Div(Field('password', placeholder='password'), css_class="form-group"),
                                    Div(Submit('submit', 'Log in',css_class='btn btn-warning')))


class myPasswordResetForm(PasswordResetForm):
    """Override password reset form using Crispy form"""
    def __init__(self,*args, **kwargs):
        super(myPasswordResetForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_show_labels = False
        self.helper.layout = Layout(Div(Field('email', placeholder=' email'), css_class="form-group"),
                                    Div(Submit('submit', 'Reset Password',css_class='btn btn-warning')))


class myPasswordResetConfirmForm(SetPasswordForm):
    """Override new password form using Crispy form"""
    def __init__(self, *args, **kwargs):
        super(myPasswordResetConfirmForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.field_class = 'col-11'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_show_labels = False
        self.helper.form_show_errors = False
        self.helper.layout = Layout(Div(Field('new_password1', placeholder='new password'), css_class="form-group"),
                                    Div(Field('new_password2', placeholder='re-enter new password'), css_class="form-group"),
                                    Div(Submit('submit', 'Set Password', css_class='btn btn-warning')))
