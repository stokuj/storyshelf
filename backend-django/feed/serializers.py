from rest_framework import serializers


class FeedActorSerializer(serializers.Serializer):
    handle = serializers.CharField()
    display_name = serializers.CharField()
    avatar_url = serializers.CharField(allow_null=True)


class FeedBookSerializer(serializers.Serializer):
    title = serializers.CharField()
    slug = serializers.SlugField()
    cover_url = serializers.CharField(allow_blank=True)


class FeedItemSerializer(serializers.Serializer):
    type = serializers.CharField()
    timestamp = serializers.DateTimeField()
    actor = FeedActorSerializer()
    book = FeedBookSerializer()
    rating = serializers.IntegerField(allow_null=True)
    body = serializers.CharField(allow_null=True)
    finish_date = serializers.DateField(allow_null=True)


class FeedResponseSerializer(serializers.Serializer):
    results = FeedItemSerializer(many=True)
    next_before = serializers.DateTimeField(allow_null=True)
