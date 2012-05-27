from django.db import models

# Create your models here.
class Customer (models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=10)
    party_size = models.PositiveSmallIntegerField()
    
    def __unicode__(self):
        return "%s (%d): %s" % (self.name, self.party_size, self.phone)
