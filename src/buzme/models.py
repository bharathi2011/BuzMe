from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Customer (models.Model):
    class CUSTOMER_STATUS:
        WAITING, SUMMON_FAILED, SUMMONED, CHECKEDIN, REMOVED = range(5)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=10)
    party_size = models.PositiveSmallIntegerField()
    waitlist = models.ForeignKey('WaitList', related_name='customers')
    status = models.PositiveSmallIntegerField(
                                              choices=((CUSTOMER_STATUS.WAITING, 'Waiting'), 
                                                       (CUSTOMER_STATUS.SUMMON_FAILED, 'Summon Failed'), 
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
    def is_summon_failed(self):
        return self.status == Customer.CUSTOMER_STATUS.SUMMON_FAILED
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
    name         = models.CharField(max_length=100)
    contactinfo  = models.CharField(max_length=200)
    def __unicode__(self):
        return self.name
    def add_waitinglist(self, waitlist):
        self.waitlists.add(waitlist)


class RestaurantAdmin (models.Model):
    adminuser  = models.OneToOneField(User, related_name='restaurantAdminUser', blank=True)
    restaurant = models.ForeignKey(Restaurant, related_name='restaurantAdministrator', unique=True)
    nick       = models.CharField(max_length=20)
    def __unicode__(self):
        return "admin for restaurant %s is %s"%(self.restaurant, self.adminuser)

class RecentActivity (models.Model):
    activity      = models.CharField(max_length=256)
    restaurant    = models.ForeignKey('Restaurant', related_name='activities')
    activityTime  = models.DateTimeField(auto_now_add=True)
    def __unicode__(self):
        return "%s %s"%(self.activityTime.strftime("%I:%M %p: "), self.activity)
