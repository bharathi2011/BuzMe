from django.test import TestCase
from models import Customer


class SimpleTest(TestCase):
    def test_customer_creation(self):
        # Save
        original_customer_count = Customer.objects.count()
        c = Customer(name="Fred", party_size=5, phone="1234567890")
        c.save()
        self.assertEqual(Customer.objects.count(), original_customer_count+1)
        c = None
        
        #Load
        c = Customer.objects.get(name="Fred")
        self.assertNotEqual(c, None)
        self.assertEqual(c.name, "Fred")
        self.assertEqual(c.party_size, 5)
        self.assertEqual(c.phone, "1234567890")
