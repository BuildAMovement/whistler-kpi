from django.conf.urls import url, include
from django.views.i18n import javascript_catalog
from django.contrib.auth import views as auth_views
from hub.views import ExtraDetailRegistrationView, TwoFactorAuth, two_factor_auth_qrcode
from rest_framework.routers import DefaultRouter
from rest_framework_extensions.routers import ExtendedDefaultRouter
from hub.forms import LoginForm

from kpi.views import (
    AssetViewSet,
    AssetVersionViewSet,
    AssetSnapshotViewSet,
    SubmissionViewSet,
    UserViewSet,
    CurrentUserViewSet,
    CollectionViewSet,
    TagViewSet,
    ImportTaskViewSet,
    ObjectPermissionViewSet,
    SitewideMessageViewSet,
    AuthorizedApplicationUserViewSet,
    OneTimeAuthenticationKeyViewSet,
    UserCollectionSubscriptionViewSet,
    TokenView,
)

from kpi.views import home, one_time_login, browser_tests
from kobo.apps.reports.views import ReportsViewSet
from kobo.apps.superuser_stats.views import user_report, retrieve_user_report
from kpi.views import authorized_application_authenticate_user
from kpi.forms import RegistrationForm
from hub.views import switch_builder

router = ExtendedDefaultRouter()
asset_routes = router.register(r'assets', AssetViewSet)
asset_routes.register(r'versions',
                      AssetVersionViewSet,
                      base_name='asset-version',
                      parents_query_lookups=['asset'],
                      )
asset_routes.register(r'submissions',
                      SubmissionViewSet,
                      base_name='submission',
                      parents_query_lookups=['asset'],
                      )


router.register(r'asset_snapshots', AssetSnapshotViewSet)
router.register(
    r'collection_subscriptions', UserCollectionSubscriptionViewSet)
router.register(r'collections', CollectionViewSet)
router.register(r'users', UserViewSet)
router.register(r'tags', TagViewSet)
router.register(r'permissions', ObjectPermissionViewSet)
router.register(r'reports', ReportsViewSet, base_name='reports')
router.register(r'imports', ImportTaskViewSet)
router.register(r'sitewide_messages', SitewideMessageViewSet)

router.register(r'authorized_application/users',
                AuthorizedApplicationUserViewSet,
                base_name='authorized_applications')
router.register(r'authorized_application/one_time_authentication_keys',
                OneTimeAuthenticationKeyViewSet)

# Apps whose translations should be available in the client code.
js_info_dict = {
    'packages': ('kobo.apps.KpiConfig',),
}

urlpatterns = [
    url(r'^$', home, name='kpi-root'),
    url(r'^me/$', CurrentUserViewSet.as_view({
        'get': 'retrieve',
        'patch': 'partial_update',
    }), name='currentuser-detail'),
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),
    url(r'^accounts/register/$', ExtraDetailRegistrationView.as_view(
        form_class=RegistrationForm), name='registration_register'),
    url(r'^accounts/twofa/?$', TwoFactorAuth.as_view(), name='two_factor_auth'),
    url(r'^accounts/twofa/qrcode/$', two_factor_auth_qrcode, name='two_factor_auth_qrcode'),
    url(r'^accounts/login/$',
        auth_views.login,
        {
            'authentication_form': LoginForm,
            'template_name': 'registration/login.html',
        },
        name='auth_login'),
    url(r'^accounts/logout/', 'django.contrib.auth.views.logout',
        {'next_page': '/'}),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(
        r'^authorized_application/authenticate_user/$',
        authorized_application_authenticate_user
    ),
    url(r'^browser_tests/$', browser_tests),
    url(r'^authorized_application/one_time_login/$', one_time_login),
    url(r'^hub/switch_builder$', switch_builder, name='toggle-preferred-builder'),
    # Translation catalog for client code.
    url(r'^jsi18n/$', javascript_catalog, js_info_dict, name='javascript-catalog'),
    # url(r'^.*', home),
    url(r'^token/$', TokenView.as_view(), name='token'),
    # Statistics for superusers
    url(r'^superuser_stats/user_report/$',
        'kobo.apps.superuser_stats.views.user_report'),
    url(r'^superuser_stats/user_report/(?P<base_filename>[^/]+)$',
        'kobo.apps.superuser_stats.views.retrieve_user_report'),
]
