from django.contrib import admin

from models import Customer, WaitList, Restaurant, RestaurantAdmin, RecentActivity, ArchiveTag

admin.site.register(Customer)
admin.site.register(WaitList)
admin.site.register(Restaurant)
admin.site.register(RestaurantAdmin)
admin.site.register(RecentActivity)
admin.site.register(ArchiveTag)
