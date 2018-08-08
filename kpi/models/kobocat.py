import re
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy, ugettext as _
from jsonfield import JSONField


class UserProfile(models.Model):
    # This field is required.
    user = models.OneToOneField(User, related_name='profile')

    # Other fields here
    name = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=2, blank=True)
    organization = models.CharField(max_length=255, blank=True)
    home_page = models.CharField(max_length=255, blank=True)
    twitter = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255, blank=True)
    require_auth = models.BooleanField(
        default=False,
        verbose_name=ugettext_lazy(
            "Require authentication to see forms and submit data"
        )
    )
    address = models.CharField(max_length=255, blank=True)
    phonenumber = models.CharField(max_length=30, blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True)
    num_of_submissions = models.IntegerField(default=0)
    metadata = JSONField(default={}, blank=True)

    def __unicode__(self):
        return u'%s[%s]' % (self.name, self.user.username)

    class Meta:
        app_label = 'main'
        db_table = 'main_userprofile'
        permissions = (
            ('can_add_xform', "Can add/upload an xform to user profile"),
            ('view_profile', "Can view user profile"),
        )


XFORM_TITLE_LENGTH = 255


class XForm(models.Model):
    CLONED_SUFFIX = '_cloned'
    MAX_ID_LENGTH = 100

    xls = models.FileField(null=True)
    json = models.TextField(default=u'')
    description = models.TextField(default=u'', null=True)
    xml = models.TextField()

    user = models.ForeignKey(User, related_name='xforms', null=True)
    require_auth = models.BooleanField(default=False)
    shared = models.BooleanField(default=False)
    shared_data = models.BooleanField(default=False)
    downloadable = models.BooleanField(default=True)
    allows_sms = models.BooleanField(default=False)
    encrypted = models.BooleanField(default=False)

    # the following fields are filled in automatically
    sms_id_string = models.SlugField(
        editable=False,
        verbose_name=ugettext_lazy("SMS ID"),
        max_length=MAX_ID_LENGTH,
        default=''
    )
    id_string = models.SlugField(
        editable=False,
        verbose_name=ugettext_lazy("ID"),
        max_length=MAX_ID_LENGTH
    )
    title = models.CharField(editable=False, max_length=XFORM_TITLE_LENGTH)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    last_submission_time = models.DateTimeField(blank=True, null=True)
    has_start_time = models.BooleanField(default=False)
    uuid = models.CharField(max_length=32, default=u'')

    uuid_regex = re.compile(r'(<instance>.*?id="[^"]+">)(.*</instance>)(.*)',
                            re.DOTALL)
    instance_id_regex = re.compile(r'<instance>.*?id="([^"]+)".*</instance>',
                                   re.DOTALL)
    uuid_node_location = 2
    uuid_bind_location = 4
    bamboo_dataset = models.CharField(max_length=60, default=u'')
    instances_with_geopoints = models.BooleanField(default=False)
    num_of_submissions = models.IntegerField(default=0)

    class Meta:
        app_label = 'logger'
        db_table = 'logger_xform'
        verbose_name = 'xform'
        verbose_name_plural = 'xforms'
        unique_together = (("user", "id_string"), ("user", "sms_id_string"))
        ordering = ("id_string",)
        permissions = (
            ("view_xform", _("Can view associated data")),
            ("report_xform", _("Can make submissions to the form")),
            ("move_xform", _(u"Can move form between projects")),
            ("transfer_xform", _(u"Can transfer form ownership.")),
        )

    def __unicode__(self):
        return getattr(self, "id_string", "")
