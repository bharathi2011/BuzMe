from django.contrib import admin

from models import Customer, WaitList, Restaurant, RestaurantAdmin

admin.site.register(Customer)
admin.site.register(WaitList)
admin.site.register(Restaurant)
admin.site.register(RestaurantAdmin)
