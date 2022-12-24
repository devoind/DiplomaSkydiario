from django.contrib import admin
from django.contrib.auth.forms import AuthenticationForm

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # date_hierarchy = 'date_joined'
    # empty_value_display = 'no data'
    # fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'date_joined', 'last_login']
    # readonly_fields = ['date_joined', 'last_login']
    # list_display = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active']
    # list_display_links = ['username', 'email', 'first_name', 'last_name']
    # list_filter = ['is_staff', 'is_active', 'is_superuser']

    fieldsets = (
        ('Info', {'fields': ('username', 'first_name', 'last_name', 'email')}),
        ('Access levels', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Login information', {'fields': ('last_login', 'date_joined')}),
    )

    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['last_login', 'date_joined']
        return self.readonly_fields

    search_fields = ('username', 'first_name', 'last_name', 'email')
    list_display_links = ('id', 'username', 'email', 'first_name', 'last_name')
    ordering = ('id',)

    # def get_list_display(self, request):
    #     return 'username', 'email', 'first_name', 'last_name'

# admin.site.register(User, UserAdmin)
