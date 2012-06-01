from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Customer (models.Model):
    class CUSTOMER_STATUS:
        WAITING, SUMMONED, CHECKEDIN, REMOVED = range(4)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=10)
    party_size = models.PositiveSmallIntegerField()
    waitlist = models.ForeignKey('WaitList', related_name='customers')
    status = models.PositiveSmallIntegerField(
                                              choices=((CUSTOMER_STATUS.WAITING, 'Waiting'), 
                                                       (CUSTOMER_STATUS.SUMMONED, 'Summoned'), 
                                                       (CUSTOMER_STATUS.CHECKEDIN, 'CheckedIn'), 
                                                       (CUSTOMER_STATUS.REMOVED, 'Removed')), 
                                              default=CUSTOMER_STATUS.WAITING)
    def __unicode__(self):
        return "%s (%d): %s (%s)" % (self.name, self.party_size, self.phone, self.get_status_display())
    def is_waiting(self):
        return self.status == Customer.CUSTOMER_STATUS.WAITING
    def is_summoned(self):
        return self.status == Customer.CUSTOMER_STATUS.SUMMONED
    def is_removed(self):
        return self.status == Customer.CUSTOMER_STATUS.REMOVED
    def is_checkedin(self):
        return self.status == Customer.CUSTOMER_STATUS.CHECKEDIN
    
class WaitList (models.Model):
    restaurant = models.ForeignKey('Restaurant', related_name='waitlists')
    
    def __unicode__(self):
        return "Waitlist for %s" % str(self.restaurant)
    
    def add_customer(self, customer):
        self.customers.add(customer)

class Restaurant (models.Model):
    name = models.CharField(max_length=100)
    user = models.OneToOneField(User)
    
    def __unicode__(self):
        return self.name
    
    
