from django.db import models

# Create your models here.
class Customer (models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=10)
    party_size = models.PositiveSmallIntegerField()
    waitlist = models.ForeignKey('WaitList', related_name='customers')
    
    def __unicode__(self):
        return "%s (%d): %s" % (self.name, self.party_size, self.phone)
    
class WaitList (models.Model):
    restaurant = models.ForeignKey('Restaurant', related_name='waitlists')
    
    def __unicode__(self):
        return "Waitlist for %s" % str(self.restaurant)
    
    def add_customer(self, customer):
        self.customers.add(customer)

class Restaurant (models.Model):
    name = models.CharField(max_length=100)
    
    
