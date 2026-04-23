from django import forms
from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from .models import AboutSystem, DynamicPages, SMTPSetting, SocialMedia, SystemColor
@admin.register(AboutSystem)

class AboutSystemAdmin(ModelAdmin):
    list_display = ("id", "name", "title", "email", "copyright", "description",)
    search_fields = ("id", "name", "title", "email", "copyright", "description",)
    list_display_links = ("id", "name", "title", "email", "copyright", "description",)

    def has_add_permission(self, request):
        return False

    # def preview_logo(self, obj):
    #     if obj.logo:
    #         return format_html(f'<img src="{obj.logo.url}" width="50" height="50" />')
    #     return "No Logo"

    # def preview_favicon(self, obj):
    #     if obj.favicon:
    #         return format_html(f'<img src="{obj.favicon.url}" width="50" height="50" />')
    #     return "No Favicon"

@admin.register(DynamicPages)
class DynamicPagesAdmin(ModelAdmin):
    list_display = ("id", "title", "status",)
    search_fields = ("id", "title", "content",)
    list_display_links = ("id", "title", "status",)


from django.urls import path, reverse
from django.shortcuts import redirect, get_object_or_404
from django.utils.html import format_html

@admin.register(SMTPSetting)
class SMTPSettingAdmin(ModelAdmin):
    list_display = (
        "id",
        "host",
        "port",
        "username",
        "encryption",
        "sender_name",
        "sender_email",
        "is_active_switch",
    )

    def is_active_switch(self, obj):
        url = reverse("admin:smtp_toggle_active", args=[obj.pk])

        return format_html(
            '<a class="button" href="{}" '
            'style="background:{};color:white;padding:5px 10px;'
            'border-radius:20px;text-decoration:none;">{}</a>',
            url,
            "green" if obj.is_active else "gray",
            "ON" if obj.is_active else "OFF",
        )

    is_active_switch.short_description = "Active"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "toggle-active/<int:pk>/",
                self.admin_site.admin_view(self.toggle_active),
                name="smtp_toggle_active",
            ),
        ]
        return custom_urls + urls

    def toggle_active(self, request, pk):
        obj = get_object_or_404(SMTPSetting, pk=pk)
        obj.is_active = not obj.is_active
        obj.save()
        return redirect(request.META.get("HTTP_REFERER", "/admin/"))

@admin.register(SocialMedia)
class SocialMediaAdmin(ModelAdmin):
    list_display = ("id", "name", "url", "preview_icon",)
    search_fields = ("id", "name", "url", "preview_icon",)
    list_display_links = ("id", "name", "url","preview_icon",)


    def preview_icon(self, obj):
        if obj.icon:
            return format_html(f'<img src="{obj.icon.url}" width="50" height="50" />')
        return "No Icon"
    



class SystemColorForm(forms.ModelForm):
    class Meta:
        model = SystemColor
        fields = '__all__'
        widgets = {
            'code': forms.TextInput(attrs={
                'type': 'color',
                'style': 'width: 670px; height: 100px;'
            })
        }


@admin.register(SystemColor)
class SystemColorAdmin(ModelAdmin):
    form = SystemColorForm
    list_display = ("id", "name", "code", "is_active",)
    search_fields = ("id", "name", "code",)
    list_display_links = ("id", "name", "code",)


