from django.test import SimpleTestCase

from characters.relations import RelationType, relation_group


class RelationGroupTests(SimpleTestCase):
    def test_known_types_map_to_groups(self):
        self.assertEqual(relation_group(RelationType.PARENT), "family")
        self.assertEqual(relation_group(RelationType.LOVER), "romance")
        self.assertEqual(relation_group(RelationType.FRIEND), "friendship")
        self.assertEqual(relation_group(RelationType.MENTOR), "mentorship")
        self.assertEqual(relation_group(RelationType.MASTER), "power")
        self.assertEqual(relation_group(RelationType.ENEMY), "conflict")
        self.assertEqual(relation_group(RelationType.OTHER), "other")

    def test_unknown_type_maps_to_other(self):
        self.assertEqual(relation_group("nonsense"), "other")

    def test_every_type_has_a_valid_group(self):
        groups = {"family", "romance", "friendship", "mentorship", "power", "conflict", "other"}
        for value in RelationType.values:
            self.assertIn(relation_group(value), groups)
