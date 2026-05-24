from rest_framework import serializers

from .models import BookCharacter, CharacterRelationship


class BookCharacterSerializer(serializers.ModelSerializer):
    mention_count = serializers.IntegerField()
    is_hidden = serializers.BooleanField()
    canonical_id = serializers.IntegerField(allow_null=True, read_only=True)

    class Meta:
        model = BookCharacter
        fields = (
            "id", "slug", "name", "description",
            "mention_count", "source", "confidence", "is_hidden",
            "canonical_id",
        )


class CharacterRelationSerializer(serializers.ModelSerializer):
    from_character_name = serializers.CharField(source="from_character.name", read_only=True)
    to_character_name = serializers.CharField(source="to_character.name", read_only=True)
    from_character_slug = serializers.CharField(source="from_character.slug", read_only=True)
    to_character_slug = serializers.CharField(source="to_character.slug", read_only=True)

    class Meta:
        model = CharacterRelationship
        fields = (
            "id",
            "from_character_name",
            "from_character_slug",
            "to_character_name",
            "to_character_slug",
            "relation_type",
        )


class AIExtractionSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    book_id = serializers.IntegerField(source="pk")
    status = serializers.CharField(source="ai_extraction_status")
    created_at = serializers.DateTimeField(source="ai_extraction_started_at")
    finished_at = serializers.DateTimeField(source="ai_extraction_finished_at")
    failure_reason = serializers.SerializerMethodField()
    characters = serializers.SerializerMethodField()
    relations = serializers.SerializerMethodField()
    covered_through = serializers.SerializerMethodField()
    confidence_summary = serializers.SerializerMethodField()

    def get_id(self, obj):
        return str(obj.pk)

    def get_failure_reason(self, obj):
        return obj.ai_extraction_failure_reason or None

    def get_characters(self, obj):
        return BookCharacterSerializer(obj.characters.all(), many=True).data

    def get_relations(self, obj):
        return CharacterRelationSerializer(obj.character_relationships.all(), many=True).data

    def get_covered_through(self, obj):
        return {
            "chapter": None,
            "percentage": 100 if obj.ai_extraction_status == "done" else None,
        }

    def get_confidence_summary(self, obj):
        visible_ai_chars = obj.characters.filter(is_hidden=False, source__in=["ai", "ai-verified"])
        confidences = [c.confidence for c in visible_ai_chars if c.confidence is not None]
        if not confidences:
            return {"overall": None, "flagged_low": 0}
        avg = sum(confidences) / len(confidences)
        flagged = sum(1 for c in confidences if c < 0.5)
        return {"overall": round(avg, 3), "flagged_low": flagged}


class MergeRequestSerializer(serializers.Serializer):
    into = serializers.IntegerField(min_value=1)
