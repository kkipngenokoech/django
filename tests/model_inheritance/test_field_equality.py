from django.db import models
from django.test import TestCase


class FieldEqualityTests(TestCase):
    """
    Test field equality behavior with abstract model inheritance.
    """

    def test_abstract_model_field_equality(self):
        """
        Fields from different models inheriting from the same abstract model
        should not be equal.
        """
        class AbstractModel(models.Model):
            class Meta:
                abstract = True
            myfield = models.IntegerField()

        class ModelA(AbstractModel):
            class Meta:
                app_label = 'test_app'

        class ModelB(AbstractModel):
            class Meta:
                app_label = 'test_app'

        field_a = ModelA._meta.get_field('myfield')
        field_b = ModelB._meta.get_field('myfield')

        # Fields should not be equal
        self.assertNotEqual(field_a, field_b)
        
        # Fields should have different hashes
        self.assertNotEqual(hash(field_a), hash(field_b))

    def test_abstract_model_field_set_deduplication(self):
        """
        Fields from different models should not be deduplicated in sets.
        """
        class AbstractModel(models.Model):
            class Meta:
                abstract = True
            myfield = models.IntegerField()

        class ModelA(AbstractModel):
            class Meta:
                app_label = 'test_app'

        class ModelB(AbstractModel):
            class Meta:
                app_label = 'test_app'

        field_a = ModelA._meta.get_field('myfield')
        field_b = ModelB._meta.get_field('myfield')

        # Set should contain both fields
        field_set = {field_a, field_b}
        self.assertEqual(len(field_set), 2)
        self.assertIn(field_a, field_set)
        self.assertIn(field_b, field_set)

    def test_same_model_field_equality(self):
        """
        Fields from the same model should still be equal (backwards compatibility).
        """
        class TestModel(models.Model):
            myfield = models.IntegerField()
            class Meta:
                app_label = 'test_app'

        field1 = TestModel._meta.get_field('myfield')
        field2 = TestModel._meta.get_field('myfield')

        # Same field should be equal to itself
        self.assertEqual(field1, field2)
        self.assertEqual(hash(field1), hash(field2))

    def test_field_ordering_stability(self):
        """
        Field ordering should remain stable for existing cases.
        """
        class TestModel(models.Model):
            field1 = models.IntegerField()
            field2 = models.CharField(max_length=100)
            class Meta:
                app_label = 'test_app'

        field1 = TestModel._meta.get_field('field1')
        field2 = TestModel._meta.get_field('field2')

        # Fields should be ordered by creation_counter
        self.assertLess(field1, field2)
        
        # Ordering should be consistent
        fields = [field2, field1]
        fields.sort()
        self.assertEqual(fields, [field1, field2])

    def test_fields_without_model_attribute(self):
        """
        Fields without a model attribute should maintain original behavior.
        """
        from django.db.models.fields import IntegerField
        
        field1 = IntegerField()
        field2 = IntegerField()
        
        # Fields with different creation_counters should not be equal
        self.assertNotEqual(field1, field2)
        
        # But a field should be equal to itself
        self.assertEqual(field1, field1)

    def test_mixed_model_and_no_model_fields(self):
        """
        Test comparison between fields with and without model attributes.
        """
        from django.db.models.fields import IntegerField
        
        class TestModel(models.Model):
            myfield = models.IntegerField()
            class Meta:
                app_label = 'test_app'

        model_field = TestModel._meta.get_field('myfield')
        standalone_field = IntegerField()
        
        # These should not be equal (different creation_counters anyway)
        self.assertNotEqual(model_field, standalone_field)
        
        # Hash should work for both
        field_set = {model_field, standalone_field}
        self.assertEqual(len(field_set), 2)

    def test_multiple_inheritance_levels(self):
        """
        Test field equality with multiple levels of inheritance.
        """
        class AbstractBase(models.Model):
            class Meta:
                abstract = True
            base_field = models.IntegerField()

        class AbstractMiddle(AbstractBase):
            class Meta:
                abstract = True
            middle_field = models.CharField(max_length=50)

        class ConcreteA(AbstractMiddle):
            class Meta:
                app_label = 'test_app'

        class ConcreteB(AbstractMiddle):
            class Meta:
                app_label = 'test_app'

        # Test base field
        base_field_a = ConcreteA._meta.get_field('base_field')
        base_field_b = ConcreteB._meta.get_field('base_field')
        self.assertNotEqual(base_field_a, base_field_b)
        
        # Test middle field
        middle_field_a = ConcreteA._meta.get_field('middle_field')
        middle_field_b = ConcreteB._meta.get_field('middle_field')
        self.assertNotEqual(middle_field_a, middle_field_b)
        
        # All fields should be unique in a set
        all_fields = {base_field_a, base_field_b, middle_field_a, middle_field_b}
        self.assertEqual(len(all_fields), 4)
