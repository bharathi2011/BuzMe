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
    url(r'^update/$', 'buzme.views.update_profile'),
    url(r'^delete/$', 'buzme.views.delete_profile'),

    # ADMIN urls
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    
    # Customer Waitlist Binding
    url(r'^customer/(\d+)/summon/$', 'buzme.views.summon_customer'),
    url(r'^customer/(\d+)/remove/$', 'buzme.views.remove_customer'),
    url(r'^customer/(\d+)/checkin/$', 'buzme.views.checkin_customer'),
    
    # Waitlist urls
    url(r'^waitlist/signout/$', 'buzme.views.signout'),
    url(r'^waitlist/(current)/$', 'buzme.views.waitlist'),
    url(r'^waitlist/archives/([^\\]+)/$', 'buzme.views.waitlist'),
    url(r'^archive_current/$', 'buzme.views.archive_current'),

    # test urls
    url(r'^test/add/days/(\d+)/patrons/(\d+)/endstates/(all)/$',  'buzme.views.test_add'),
    url(r'^test/add/days/(\d+)/patrons/(\d+)/endstates/(checkedin_removed)/$',  'buzme.views.test_add'),
    url(r'^test/purgeall/$', 'buzme.views.test_purgeall'),

    # Debug urls 
    url(r'^debug/misc/$', 'buzme.views.debug_misc'),
    url(r'^customers/$', 'buzme.views.debug_customers_all'),
)
