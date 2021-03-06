from django.shortcuts import redirect
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.base import TemplateView, ContextMixin
from django.views.generic.edit import DeleteView
from django.urls import reverse
from django.contrib import messages
from django.forms.models import inlineformset_factory
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from genres.models import Genre
from goods.models import Good, GoodImage
from goods.forms import GoodForm
from generic.mixins import CategoryListMixin, PageNumberMixin
from generic.controllers import PageNumberView

GoodImagesFormset = inlineformset_factory(Good, GoodImage, can_order = True, fields = "__all__")

class SortMixin(ContextMixin):
  sort = "0"
  order = "A"

  def get_context_data(self, **kwargs):
    context = super(SortMixin, self).get_context_data(**kwargs)
    context["sort"] = self.sort
    context["order"] = self.order
    return context

class SearchMixin(ContextMixin):
  search = ""

  def get_context_data(self, **kwargs):
    context = super(SearchMixin, self).get_context_data(**kwargs)
    context["search"] = self.search
    return context


class GoodsListView(PageNumberView, ListView, SortMixin, CategoryListMixin, SearchMixin):
  model = Good
  template_name = "goods_index.html"
  paginate_by = 2
  cat = None

  def get(self, request, *args, **kwargs):
    if self.kwargs["pk"] == None:
      self.cat = Genre.objects.first()
    else:
      self.cat = Genre.objects.get(pk = self.kwargs["pk"])
    return super(GoodsListView, self).get(request, *args, **kwargs)

  def get_context_data(self, **kwargs):
    context = super(GoodsListView, self).get_context_data(**kwargs)
    context["genre"] = self.cat
    return context

  def get_queryset(self):
    goods = Good.objects.filter(genre = self.cat)
    if self.search:
      goods = goods.filter(Q(name__contains = self.search) | Q(author__contains = self.search))
    if self.sort == "1":
      if self.order == "D":
        goods = goods.order_by("-price", "name")
      else:
        goods = goods.order_by("price", "name")
    else:
      if self.order == "D":
        goods = goods.order_by("-name")
      else:
        goods = goods.order_by("name")
    return goods

class GoodDetailView(PageNumberView, DetailView, SortMixin, PageNumberMixin):
  model = Good
  template_name = "good.html"

class GoodCreate(PageNumberView, TemplateView, SortMixin, PageNumberMixin):
  template_name = "good_add.html"
  cat = None
  form = None
  formset = None

  def get(self, request, *args, **kwargs):
    if self.kwargs["pk"] == None:
      self.cat = Genre.objects.first()
    else:
      self.cat = Genre.objects.get(pk = self.kwargs["pk"])
    self.form = GoodForm(initial = {"genre": self.cat})
    self.formset = GoodImagesFormset()
    return super(GoodCreate, self).get(request, *args, **kwargs)

  def get_context_data(self, **kwargs):
    context = super(GoodCreate, self).get_context_data(**kwargs)
    context["genre"] = self.cat
    context["form"] = self.form
    context["formset"] = self.formset
    return context

  def post(self, request, *args, **kwargs):
    self.form = GoodForm(request.POST, request.FILES)
    if self.form.is_valid():
      new_good = self.form.save()
      self.formset = GoodImagesFormset(request.POST, request.FILES, instance = new_good)
      if self.formset.is_valid():
        self.formset.save()
        messages.add_message(request, messages.SUCCESS, "Товар успешно добавлен")
        return redirect(reverse("goods_index", kwargs = {"pk": new_good.genre.pk}) + "?page=" + self.request.GET["page"] + "&sort=" + self.request.GET["sort"] + "&order=" + self.request.GET["order"])
    if self.kwargs["pk"] == None:
      self.cat = Genre.objects.first()
    else:
      self.cat = Genre.objects.get(pk = self.kwargs["pk"])
    self.formset = GoodImagesFormset(request.POST, request.FILES)
    return super(GoodCreate, self).get(request, *args, **kwargs)

class GoodUpdate(PageNumberView, TemplateView, SortMixin, PageNumberMixin):
  good = None
  template_name = "good_edit.html"
  form = None
  formset = None

  def get(self, request, *args, **kwargs):
    self.good = Good.objects.get(pk = self.kwargs["pk"])
    self.form = GoodForm(instance = self.good)
    self.formset = GoodImagesFormset(instance = self.good)
    return super(GoodUpdate, self).get(request, *args, **kwargs)

  def get_context_data(self, **kwargs):
    context = super(GoodUpdate, self).get_context_data(**kwargs)
    context["good"] = self.good
    context["form"] = self.form
    context["formset"] = self.formset
    return context

  def post(self, request, *args, **kwargs):
    self.good = Good.objects.get(pk = self.kwargs["pk"])
    self.form = GoodForm(request.POST, request.FILES, instance = self.good)
    self.formset = GoodImagesFormset(request.POST, request.FILES, instance = self.good)
    if self.form.is_valid():
      self.form.save()
      if self.formset.is_valid():
        self.formset.save()
        messages.add_message(request, messages.SUCCESS, "Товар успешно изменен")
        return redirect(reverse("goods_index", kwargs = {"pk": self.good.genre.pk}) + "?page=" + self.request.GET["page"] + "&sort=" + self.request.GET["sort"] + "&order=" + self.request.GET["order"])
    return super(GoodUpdate, self).get(request, *args, **kwargs)

class GoodDelete(PageNumberView, DeleteView, SortMixin, PageNumberMixin):
  model = Good
  template_name = "good_delete.html"
  
  def post(self, request, *args, **kwargs):
    self.success_url = reverse("goods_index", kwargs = {"pk": Good.objects.get(pk = kwargs["pk"]).genre.pk}) + "?page=" + self.request.GET["page"] + "&sort=" + self.request.GET["sort"] + "&order=" + self.request.GET["order"]
    messages.add_message(request, messages.SUCCESS, "Товар успешно удален")
    return super(GoodDelete, self).post(request, *args, **kwargs)
