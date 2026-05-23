from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=255, unique=True)
    bio = models.TextField(blank=True, default="")
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name


class Serie(models.Model):  # "Series" clashes with Django test internals
    class Status(models.TextChoices):
        ONGOING = "ONGOING"
        COMPLETED = "COMPLETED"
        CANCELLED = "CANCELLED"
        HIATUS = "HIATUS"

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "series"

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
