from django.contrib import admin

from wiki.models import Page, PageVersion

admin.site.register(Page)
admin.site.register(PageVersion)
