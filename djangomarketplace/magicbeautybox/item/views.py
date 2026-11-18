from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .forms import NewItemForm, EditItemForm

from .models import category, Item

ITEMS_PER_PAGE = 12


def items(request):
    query = request.GET.get('query', '')
    try:
        category_id = int(request.GET.get('category', 0))
    except ValueError:
        category_id = 0
    categories = category.objects.all()
    items = Item.objects.filter(is_sold=False).select_related('created_by').order_by('-created_at', '-pk')

    if category_id:
        items = items.filter(category_id=category_id)

    if query:
        items = items.filter(Q(name__icontains=query) | Q(description__icontains=query))

    paginator = Paginator(items, ITEMS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Filtros para los enlaces de paginación (sin 'page', que se agrega en la plantilla)
    filter_params = urlencode({'query': query, 'category': category_id or ''})

    return render(request, 'item/items.html', {
        'items': page_obj.object_list,
        'page_obj': page_obj,
        'filter_params': filter_params,
        'query': query,
        'categories': categories,
        'category_id': category_id,
    })


def detail(request, pk):
    item = get_object_or_404(Item.objects.select_related('created_by'), pk=pk)
    related_items = Item.objects.filter(category=item.category, is_sold=False).select_related('created_by').exclude(pk=pk)[0:3]

    return render(request, 'item/detail.html', {
        'item': item,
        'related_items': related_items
    })

@login_required
def new(request):
    if request.method == 'POST':
        form = NewItemForm(request.POST, request.FILES)

        if form.is_valid():
            item = form.save(commit=False)
            item.created_by = request.user
            item.save()

            return redirect('item:detail', pk=item.id)
    else:
        form = NewItemForm()

    return render(request, 'item/form.html', {
        'form': form,
        'title': 'Nuevo artículo',
    })

@login_required
def edit(request, pk):
    item = get_object_or_404(Item, pk=pk, created_by=request.user)

    if request.method == 'POST':
        form = EditItemForm(request.POST, request.FILES, instance=item)

        if form.is_valid():
            form.save()

            return redirect('item:detail', pk=item.id)
    else:
        form = EditItemForm(instance=item)

    return render(request, 'item/form.html', {
        'form': form,
        'title': 'Editar artículo',
    })


@login_required
@require_POST
def delete(request, pk):
    item = get_object_or_404(Item, pk=pk, created_by=request.user)
    item.delete()

    return redirect('dashboard:index')
