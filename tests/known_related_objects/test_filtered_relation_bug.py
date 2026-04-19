from django.db.models import FilteredRelation
from django.test import TestCase

from .models import PoolStyle


class TestFilteredRelationBug(TestCase):
    @classmethod
    def setUpTestData(cls):
        from .models import Tournament, Pool, Organiser
        cls.t1 = Tournament.objects.create(name="Tourney 1")
        cls.o1 = Organiser.objects.create(name="Organiser 1")
        cls.p1 = Pool.objects.create(
            name="T1 Pool 1", tournament=cls.t1, organiser=cls.o1
        )
        cls.ps1 = PoolStyle.objects.create(name="T1 Pool 1 Style", pool=cls.p1)

    def test_issue_reproduction(self):
        p = list(PoolStyle.objects.annotate(
            tournament_pool=FilteredRelation('pool__tournament__pool'),
        ).select_related('tournament_pool'))
        # This should pass but fails because tournament_pool.tournament
        # incorrectly references a PoolStyle object instead of Tournament
        self.assertEqual(p[0].pool.tournament, p[0].tournament_pool.tournament)