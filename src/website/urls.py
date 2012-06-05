from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'website.views.home', name='home'),
    # url(r'^website/', include('website.foo.urls')),

    # Login page
    url(r'^$', 'buzme.views.signin_new'),

    # signup page
    url(r'^signup/$', 'buzme.views.signup'),

    # signout redirect page
    url(r'^signout/$', 'buzme.views.signout'),

    # update profile page
    url(r'^update/$', 'buzme.views.update'),

    # ADMIN urls
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    
    # Customer to Waitlist Binding
    url(r'^customer/(\d+)/summon/$', 'buzme.views.summon_customer'),
    url(r'^customer/(\d+)/remove/$', 'buzme.views.remove_customer'),
    url(r'^customer/(\d+)/checkin/$', 'buzme.views.checkin_customer'),
    url(r'^customers/create_in_waitlist/(\d+)/$', 'buzme.views.add_customer_to_waitlist'),
    
    # Waitlist urls
    url(r'^landing/$', 'buzme.views.landing'),
    url(r'^landing/signout/$', 'buzme.views.signout'),
    
    # Debug urls 
    url(r'^debug/misc/$', 'buzme.views.debug_misc'),
    url(r'^customers/$', 'buzme.views.debug_customers_all'),
)
