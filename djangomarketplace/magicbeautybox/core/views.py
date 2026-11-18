from django.db.models import Count, Q
from django.shortcuts import render, redirect
from item.models import category, Item
from .forms import SignupForm


def index(request):
    items = Item.objects.filter(is_sold=False).select_related('created_by').order_by('-created_at')[0:6]
    categories = category.objects.annotate(num_items=Count('items', filter=Q(items__is_sold=False)))

    return render(request, 'core/index.html', {
        'categories': categories,
        'items': items,
    })

def contact(request):
    return render(request, 'core/contact.html')

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect('core:login')
    else:
        form = SignupForm()

    return render(request, 'core/signup.html', {
        'form': form
    })
