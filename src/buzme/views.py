# Create your views here.
from django.shortcuts import render_to_response

from models import Customer

def debug_customers_all(request):
    return render_to_response('buzme/debug_customers.html',
                              {'customers_qs': Customer.objects.all()})
