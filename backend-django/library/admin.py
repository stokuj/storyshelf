from django.contrib import admin
from .models import Author, Serie, Tag


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "birth_date")
    search_fields = ("name",)


@admin.register(Serie)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ("name", "status")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
