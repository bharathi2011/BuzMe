from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'website.views.home', name='home'),
    # url(r'^website/', include('website.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    
    url(r'^customer/(\d+)/summon/$', 'buzme.views.summon_customer'),
    url(r'^customer/(\d+)/remove/$', 'buzme.views.remove_customer'),
    url(r'^customer/(\d+)/checkin/$', 'buzme.views.checkin_customer'),
    url(r'^customers/create_in_waitlist/(\d+)/$', 'buzme.views.create_in_waitlist'),
    
    url(r'^waitlist/(\d+)/$', 'buzme.views.show_waitlist'),
    
    url(r'^restaurant/(\d+)/signin/$', 'buzme.views.signin'),
    url(r'^restaurant/(\d+)/signout/$', 'buzme.views.signout'),
    
    # debug 
    url(r'^debug/misc/$', 'buzme.views.debug_misc'),
    url(r'^customers/$', 'buzme.views.debug_customers_all'),
)
