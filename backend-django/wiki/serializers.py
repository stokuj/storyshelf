from rest_framework import serializers

from wiki.models import Page, PageVersion


class PageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ["path", "type", "title", "book", "universe"]


class PageSerializer(serializers.ModelSerializer):
    version = serializers.IntegerField(read_only=True)

    class Meta:
        model = Page
        fields = ["path", "type", "title", "book", "universe", "content", "version"]


class PageCreateSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=Page.Type.choices)
    title = serializers.CharField(max_length=200)
    author = serializers.CharField(max_length=200, required=False)
    year = serializers.IntegerField(required=False)
    book = serializers.CharField(required=False)
    universe = serializers.CharField(required=False)


class PageEditSerializer(serializers.Serializer):
    # Stored byte for byte, so no trimming
    content = serializers.CharField(trim_whitespace=False)
    base_version = serializers.IntegerField()


class PageVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageVersion
        fields = ["id", "kind", "author", "content", "created_at"]
