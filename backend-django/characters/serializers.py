from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Character


class CharacterListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Character
        fields = ["name", "slug", "role"]


class CharacterRelationSerializer(serializers.Serializer):
    to_slug = serializers.CharField(source="to_character.slug")
    to_name = serializers.CharField(source="to_character.name")
    type = serializers.CharField(source="relation_type")
    type_display = serializers.CharField(source="get_relation_type_display")
    group = serializers.CharField()


class CharacterDetailSerializer(serializers.ModelSerializer):
    relations = serializers.SerializerMethodField()

    class Meta:
        model = Character
        fields = ["name", "slug", "role", "description", "relations"]

    @extend_schema_field(CharacterRelationSerializer(many=True))
    def get_relations(self, obj):
        return CharacterRelationSerializer(obj.relations_from.all(), many=True).data


class CharacterListResponseSerializer(serializers.Serializer):
    status = serializers.CharField(allow_null=True)
    characters = CharacterListSerializer(many=True)
