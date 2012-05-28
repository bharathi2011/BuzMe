# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse
from models import Customer, WaitList

def debug_customers_all(request):
    return render_to_response('buzme/debug_customers.html',
                              {'customers_qs': Customer.objects.all()})
    
def summon_customer(request, customer_id):
    return set_customer_status(request, customer_id, Customer.CUSTOMER_STATUS.SUMMONED)

def remove_customer(request, customer_id):
    return set_customer_status(request, customer_id, Customer.CUSTOMER_STATUS.REMOVED)

# Helper for summon_customer and remove_customer
def set_customer_status(request, customer_id, status):
    c = get_object_or_404(Customer, pk=customer_id)
    c.status = status
    c.save()
    return redirect('/waitlist/%d/' % c.waitlist.id)
   
def show_waitlist(request, waitlist_id):
    wl = get_object_or_404(WaitList, pk=waitlist_id)
    return render_to_response('buzme/waitlist.html',
                              {'waitlist': wl})
    
def debug_misc(request):
    '''Use this however you want, it's accessible from /debug/misc. Leave it as you found it, though.'''
    return HttpResponse('Howdy! This is a debug view where devs can do anything they want between check-ins')
    
        
    
