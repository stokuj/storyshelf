from rest_framework import serializers

from .models import Character


class CharacterListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Character
        fields = ["name", "slug", "role"]


class CharacterRelationSerializer(serializers.Serializer):
    to_slug = serializers.CharField(source="to_character.slug")
    to_name = serializers.CharField(source="to_character.name")
    label = serializers.CharField()


class CharacterDetailSerializer(serializers.ModelSerializer):
    relations = serializers.SerializerMethodField()

    class Meta:
        model = Character
        fields = ["name", "slug", "role", "description", "relations"]

    @staticmethod
    def get_relations(obj):
        return CharacterRelationSerializer(obj.relations_from.all(), many=True).data


class CharacterListResponseSerializer(serializers.Serializer):
    status = serializers.CharField(allow_null=True)
    characters = CharacterListSerializer(many=True)
