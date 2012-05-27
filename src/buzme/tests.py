from django.test import TestCase
from models import Customer, WaitList, Restaurant


def save_load(obj):
    obj.save()
    return obj.__class__.objects.get(pk=obj.id)

class CustomerTest(TestCase):
    def test_customer_creation(self):
        # Save
        original_customer_count = Customer.objects.count()
        r = Restaurant(name="Slippery Bannana"); r.save();
        wl = WaitList(restaurant = r); wl.save()
        c = Customer(name="Fred", party_size=5, phone="1234567890", waitlist=wl)
        c = save_load(c)
        self.assertEqual(Customer.objects.count(), original_customer_count+1)
        self.assertNotEqual(c, None)
        self.assertEqual(c.name, "Fred")
        self.assertEqual(c.party_size, 5)
        self.assertEqual(c.phone, "1234567890")

class WaitListTest(TestCase):
    def test_add_customer(self):
        r = Restaurant(name="Slippery Bannana"); r.save();
        wl = WaitList(restaurant = r); wl.save()
        wl.add_customer(Customer(name="Fred", party_size=5, phone="1234567890", waitlist=wl))
        wl.add_customer(Customer(name="George", party_size=2, phone="1112223333", waitlist=wl))
        wl = save_load(wl);
        self.assertEqual(wl.customers.count(), 2)
        self.assertEqual(wl.customers.filter(name="Fred").count(), 1)
        self.assertEqual(wl.customers.filter(name="George").count(), 1)