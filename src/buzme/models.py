from django.db import models
from django.contrib.auth.models import User
import datetime

# Create your models here.
class Customer (models.Model):
    class CUSTOMER_STATUS:
        WAITING, SUMMON_FAILED, SUMMONED, CHECKEDIN, REMOVED = range(5)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=10)
    party_size = models.PositiveSmallIntegerField()
    waitlist = models.ForeignKey('WaitList', related_name='customers')
    dateTag = models.CharField(max_length=20)
    activityTime  = models.DateTimeField(auto_now_add=True)
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
    restaurant   = models.ForeignKey('Restaurant', related_name='waitlists')
    def __unicode__(self):
        return "Waitlist for %s" % str(self.restaurant)
    def add_customer(self, customer):
        self.customers.add(customer)
    def get_create_date(self):
        return "%s"%(self.activityTime.strftime("%m %d %y"))
    def check_waitlist_expiry(self):
        t = DateTimeField()


class Restaurant (models.Model):
    name              = models.CharField(max_length=100)
    contactinfo       = models.CharField(max_length=200)
    qrfile            = models.CharField(max_length=50)
    client_gmt_offset = models.SmallIntegerField()
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
    activity = models.PositiveSmallIntegerField(
                                              choices=((Customer.CUSTOMER_STATUS.WAITING, 'Waiting'), 
                                                       (Customer.CUSTOMER_STATUS.SUMMON_FAILED, 'Summon Failed'), 
                                                       (Customer.CUSTOMER_STATUS.SUMMONED, 'Summoned'), 
                                                       (Customer.CUSTOMER_STATUS.CHECKEDIN, 'CheckedIn'), 
                                                       (Customer.CUSTOMER_STATUS.REMOVED, 'Removed')), 
                                             )
    customer      = models.ForeignKey('Customer', related_name='activities')
    restaurant    = models.ForeignKey('Restaurant', related_name='activities')
    activityTime  = models.DateTimeField(auto_now_add=True)
    dateTag       = models.CharField(max_length=20)
    def __unicode__(self):
       lt = self.activityTime + datetime.timedelta(minutes=-self.restaurant.client_gmt_offset) 
       return "%s %s"%(lt.strftime("%b%d %I:%M %p: "), self.activity)
    def time_str(self):
       lt = self.activityTime + datetime.timedelta(minutes=-self.restaurant.client_gmt_offset) 
       return "%s"%(lt.strftime("%I:%M %p"))
    def date_str(self):
       lt = self.activityTime + datetime.timedelta(minutes=-self.restaurant.client_gmt_offset) 
       return "%s"%(lt.strftime("%b%d"))
    def activity_str(self):
       return "%s"%(self.activity)
    def hour(self):
       lt = self.activityTime + datetime.timedelta(minutes=-self.restaurant.client_gmt_offset) 
       return lt.hour
    def letter_display(self):
       return self.get_activity_display()[0:1]


class ArchiveTag (models.Model):
    restaurant    = models.ForeignKey('Restaurant', related_name='archivedtags')
    dateTag       = models.CharField(max_length=20)
    abstime       = models.DateTimeField()
    def __unicode__(self):
        return "%s"%(self.dateTag)
    @staticmethod
    def addTag(r, t):
        t1 = t + datetime.timedelta(minutes=-r.client_gmt_offset)
        tag = t1.strftime("%b %d")
        if not ArchiveTag.objects.filter(restaurant__exact=r).filter(dateTag__exact=tag).exists():
            at = ArchiveTag(dateTag=tag, restaurant=r, abstime = t)
            at.save()
        return tag

class Analytics (models.Model):
    restaurant      = models.ForeignKey('Restaurant', related_name='analytics')
    dateTag         = models.CharField(max_length=20)
    averagewaittime = models.CommaSeparatedIntegerField(max_length=5*24) 
    checkincount    = models.CommaSeparatedIntegerField(max_length=5*24) 
    def __unicode__(self):
       return "%s %s"%(self.averagewaittime, self.checkincount)
    def print_averagewaittime(self):
       return "%s"%(eval(self.averagewaittime))
    def print_checkincount(self):
       return "%s"%(eval(self.checkincount))
