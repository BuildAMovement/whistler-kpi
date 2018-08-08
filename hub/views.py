from django.contrib.auth.decorators import login_required
from django.core.management import call_command
from django.db import transaction
from django.http import HttpResponseRedirect
from registration.backends.default.views import RegistrationView
from registration.forms import RegistrationForm
from rest_framework.decorators import api_view
from django.views.generic.edit import View, FormView
from hub.forms import TwoFactorAuthFormEnabled, TwoFactorAuthFormDisabled
from django.shortcuts import render, redirect
from django_otp import user_has_device, devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.http import HttpResponse

from kpi.tasks import sync_kobocat_xforms, import_survey_drafts_from_dkobo
from .models import FormBuilderPreference, ExtraUserDetail

# The `api_view` decorator allows authentication via DRF
@api_view(['GET'])
@login_required
def switch_builder(request):
    '''
    very un-restful, but for ease of testing, a quick 'GET' is hard to beat
    '''
    if 'beta' in request.GET:
        beta_val = request.GET.get('beta') == '1'
        (pref, created) = FormBuilderPreference.objects.get_or_create(
            user=request.user)
        pref.preferred_builder = FormBuilderPreference.KPI if beta_val \
            else FormBuilderPreference.DKOBO
        pref.save()
    if 'migrate' in request.GET:
        if 'async' in request.GET:
            # Optionally run these tasks in the background to avoid bogging
            # down the app server (See
            # https://github.com/kobotoolbox/kpi/issues/1437)
            import_dkobo_func = import_survey_drafts_from_dkobo.delay
            sync_kobocat_func = sync_kobocat_xforms.delay
        else:
            import_dkobo_func = import_survey_drafts_from_dkobo
            sync_kobocat_func = sync_kobocat_xforms
        # TODO: don't start these tasks for if they're already running for this
        # particular user
        import_dkobo_func(
            username=request.user.username,
            quiet=True # squelches `print` statements
        )
        # Create/update KPI assets to match the user's KC forms
        sync_kobocat_func(username=request.user.username)

    return HttpResponseRedirect('/')


def two_factor_auth_qrcode(request, *args, **kwargs):
    user = request.user
    if (not request.user) or (not request.user.is_authenticated()):
        response = HttpResponse('', status=503)
    try:
        device = next(devices_for_user(user))

        import qrcode
        import qrcode.image.svg

        img = qrcode.make(device.config_url, image_factory=qrcode.image.svg.SvgImage)
        response = HttpResponse(content_type='image/svg+xml')
        img.save(response)
    except:
        response = HttpResponse('', status=503)

    return response
    
    
class TwoFactorAuth(View):
    def dispatch(self, request, *args, **kwargs):
        if (not request.user) or (not request.user.is_authenticated()):
            return HttpResponseRedirect('/')
        return super(TwoFactorAuth, self).dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        user = request.user
        tfa_activated = user_has_device(user) 
        if tfa_activated:
            form = TwoFactorAuthFormEnabled(prefix='to_enable')
        else:
            form = TwoFactorAuthFormDisabled(prefix='to_disable')
        return render(
            request,
            'registration/2fa.html',
            {
                'form': form,
                'tfa_activated': tfa_activated,
            },
        )
        
    def post(self, request, *args, **kwargs):
        user = request.user
        tfa_activated = user_has_device(user) 
        reqdata = request.POST.copy()
        if tfa_activated:
            form = TwoFactorAuthFormEnabled(prefix='to_enable', data=reqdata)
            if form.is_valid():
                if form.cleaned_data['status']:
                    for device in devices_for_user(user):
                        device.delete()
                return render(
                    request,
                    'registration/2fa-disabled-now.html',
                    {
                        'form': form,
                        'tfa_activated': tfa_activated,
                        'status_changed': form.cleaned_data['status'] 
                    },
                )
            else:
                return render(
                    request,
                    'registration/2fa.html',
                    {
                        'form': form,
                        'tfa_activated': tfa_activated,
                    },
                )
        else:
            form = TwoFactorAuthFormDisabled(prefix='to_disable', data=reqdata)
            if form.is_valid():
                if form.cleaned_data['status']:
                    device = TOTPDevice(user=user, name=user.username + '\'s device')
                    device.save()
    
                from base64 import b32encode
                secret_key = b32encode(device.bin_key)
    
                return render(
                    request,
                    'registration/2fa-enabled-now.html',
                    {
                        'form': form,
                        'tfa_activated': tfa_activated,
                        'status_changed': form.cleaned_data['status'],
                        'device': device,
                        'secret_key': secret_key,
                    },
                ) 
            else:
                return render(
                    request,
                    'registration/2fa.html',
                    {
                        'form': form,
                        'tfa_activated': tfa_activated,
                    },
                )
                

class ExtraDetailRegistrationView(RegistrationView):
    
    def dispatch(self, *args, **kwargs):
        return redirect('/')
                        
        """
        Check that user signup is allowed before even bothering to
        dispatch or do other processing.

        """
        if not self.registration_allowed():
            return redirect(self.disallowed_url)
        return super(ExtraDetailRegistrationView, self).dispatch(*args, **kwargs)
    
    def register(self, request, form, *args, **kwargs):
        ''' Save all the fields not included in the standard `RegistrationForm`
        into the JSON `data` field of an `ExtraUserDetail` object '''
        standard_fields = set(RegistrationForm().fields.keys())
        extra_fields = set(form.fields.keys()).difference(standard_fields)
        # Don't save the user unless we successfully store the extra data
        with transaction.atomic():
            new_user = super(ExtraDetailRegistrationView, self).register(
                request, form, *args, **kwargs)
            extra_data = {k: form.cleaned_data[k] for k in extra_fields}
            new_user.extra_details.data.update(extra_data)
            new_user.extra_details.save()
        return new_user
