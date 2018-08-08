from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.contrib.auth.hashers import (
    check_password, is_password_usable, make_password,
)
from models import SitewideMessage
from actions import delete_related_objects

class UserResource(resources.ModelResource):
 
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password',)
        export_order = fields
        import_id_fields = ('username',)
        
    def before_save_instance(self, instance, using_transactions, dry_run):
        if not is_password_usable(instance.password):
            instance.password = make_password(instance.password, None, 'pbkdf2_sha256')


class UserDeleteRelatedAdmin(ImportExportModelAdmin, UserAdmin):
    actions = [delete_related_objects]
    resource_class = UserResource


admin.site.register(SitewideMessage)
admin.site.unregister(User)
admin.site.register(User, UserDeleteRelatedAdmin)
