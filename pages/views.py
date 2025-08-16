from django.shortcuts import render, get_object_or_404, redirect
from .models import Page
from django.contrib.auth.decorators import login_required
from .forms import PageForm

# Dynamic page detail (catch-all by slug)
def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug)
    return render(request, "pages/page_detail.html", {"page": page})

@login_required
def page_list(request):
    pages = Page.objects.all()
    return render(request, "dashboard/pages/page_list.html", {"pages": pages})

@login_required
def page_create(request):
    if request.method == "POST":
        form = PageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("page_list")
    else:
        form = PageForm()
    return render(request, "dashboard/pages/create.html", {"form": form})

@login_required
def page_edit(request, pk):
    page = get_object_or_404(Page, pk=pk)
    if request.method == "POST":
        form = PageForm(request.POST, instance=page)
        if form.is_valid():
            form.save()
            return redirect("page_list")
    else:
        form = PageForm(instance=page)
    return render(request, "dashboard/pages/edit.html", {"form": form, "page": page})

@login_required
def page_delete(request, pk):
    page = get_object_or_404(Page, pk=pk)
    if request.method == "POST":
        page.delete()
        return redirect("dashboard_pages")
    return render(request, "dashboard/pages/delete.html", {"page": page})