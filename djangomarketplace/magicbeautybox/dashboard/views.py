from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from item.models import Item

@login_required
def index(request):
    items = Item.objects.filter(created_by=request.user).select_related('created_by').order_by('-created_at', '-pk')

    return render(request, 'dashboard/index.html', {
        'items': items,
    })
    
   