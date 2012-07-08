from django.test import TestCase
from models import Customer, WaitList, Restaurant, RestaurantAdmin
from django.contrib.auth.models import User
import views
from django.http import HttpRequest

def save_load(obj):
    obj.save()
    return obj.__class__.objects.get(pk=obj.id)

class CustomerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('CustomerTest_User')
        self.restaurant = Restaurant(name="Slippery Bannana", 
                                     contactinfo="123 Fake Street",
                                     qrfile="nonexistent qrfile",
                                     client_gmt_offset=1);
        self.restaurant.save();
        
    def test_customer_creation(self):
        # Save
        original_customer_count = Customer.objects.count()
        
        wl = WaitList(restaurant=self.restaurant); wl.save()
        c = Customer(name="Fred", party_size=5, phone="1234567890", waitlist=wl)
        c = save_load(c)
        self.assertEqual(Customer.objects.count(), original_customer_count+1)
        self.assertNotEqual(c, None)
        self.assertEqual(c.name, "Fred")
        self.assertEqual(c.party_size, 5)
        self.assertEqual(c.phone, "1234567890")

class WaitListTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('WaitListTest_User')
        self.user.save()
        self.restaurant = Restaurant(name="Slippery Bannana", 
                                     contactinfo="123 Fake Street",
                                     qrfile="nonexistent qrfile",
                                     client_gmt_offset=1);
        self.restaurant.save();

    def test_add_customer(self):
        wl = WaitList(restaurant=self.restaurant); 
        wl.save()
        wl.add_customer(Customer(name="Fred", party_size=5, phone="1234567890", waitlist=wl))
        wl.add_customer(Customer(name="George", party_size=2, phone="1112223333", waitlist=wl))
        wl = save_load(wl);
        self.assertEqual(wl.customers.count(), 2)
        self.assertEqual(wl.customers.filter(name="Fred").count(), 1)
        self.assertEqual(wl.customers.filter(name="George").count(), 1)
        
class TestAddTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("TestAddTest_User")
        self.restaurant = Restaurant(name="Slippery Bannana", 
                             contactinfo="123 Fake Street",
                             qrfile="nonexistent qrfile",
                             client_gmt_offset=1);
        self.restaurant.save()
        wl = WaitList(restaurant=self.restaurant); 
        wl.save()
        self.user.restaurantAdminUser = RestaurantAdmin(nick="TestAddTest_nick",
                                                        restaurant=self.restaurant) 
        self.request = HttpRequest()
        self.request.user = self.user
    
    def test_add_single(self):
        response = views.test_add(self.request, 1, 1, "all")
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/waitlist/current')
        
    def test_add_many(self):
        response = views.test_add(self.request, 3, 5, "checkedin_removed")
        self.assertEqual(Customer.objects.count(), 15)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/archive_current/')
        
class TestArchiveCurrent(TestCase):
    def setUp(self):
        '''Add user data so we have something to archive'''
        self.user = User.objects.create_user("TestAddTest_User")
        self.restaurant = Restaurant(name="Slippery Bannana", 
                             contactinfo="123 Fake Street",
                             qrfile="nonexistent qrfile",
                             client_gmt_offset=1);
        self.restaurant.save()
        wl = WaitList(restaurant=self.restaurant); 
        wl.save()
        self.user.restaurantAdminUser = RestaurantAdmin(nick="TestAddTest_nick",
                                                        restaurant=self.restaurant) 
        self.request = HttpRequest()
        self.request.user = self.user
        views.test_add(self.request, 3, 7, "checkedin_removed")
    
    def test_archive_current(self):
        response = views.archive_current(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/waitlist/current/')