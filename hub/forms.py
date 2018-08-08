from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import AuthenticationForm
from django_otp.forms import OTPAuthenticationFormMixin
from django_otp import user_has_device, devices_for_user, match_token
from django_otp.models import Device


class TwoFactorAuthFormEnabled(forms.Form):
    
    status = forms.BooleanField(label=_('I want to disable Two-Factor Authentication'))

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(TwoFactorAuthFormEnabled, self).__init__(*args, **kwargs)
        
        
class TwoFactorAuthFormDisabled(forms.Form):
    
    status = forms.BooleanField(label=_('I want to enable Two-Factor Authentication'))

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(TwoFactorAuthFormDisabled, self).__init__(*args, **kwargs)
        
        
class LoginForm(OTPAuthenticationFormMixin, AuthenticationForm):
    otp_token = forms.CharField(
        required=False, 
        help_text=_('Leave blank if you have not activated Two Factor Authentication'),
        label=_('Verification code'),
    )

    def clean(self):
        self.cleaned_data = super(LoginForm, self).clean()
        if user_has_device(self.get_user()): 
            self.clean_otp(self.get_user())

        if not self.get_user().is_staff:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )

        return self.cleaned_data
