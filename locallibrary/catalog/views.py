import datetime
from django.shortcuts import render, get_object_or_404
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .forms import RenewBookForm
from .models import Book, Author, BookInstance, Genre, Language


# Create your views here.
def index(request: HttpRequest):
    """
    View function for home page of site.
    """
    num_books = Book.objects.count()
    num_instances = BookInstance.objects.count()
    num_instances_available = BookInstance.objects.filter(status__exact="a").count()
    num_authors = Author.objects.count()

    num_visits = request.session.get("num_visits", 1)
    request.session["num_visits"] = num_visits + 1

    context = {
        "num_books": num_books,
        "num_instances": num_instances,
        "num_instances_available": num_instances_available,
        "num_authors": num_authors,
        "num_visits": num_visits,
    }
    return render(request, "index.html", context=context)


from django.views import generic


class BookListView(generic.ListView):
    model = Book
    paginate_by = 2


class BookDetailView(generic.DetailView):
    model = Book


class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10


class AuthorDetailView(generic.DetailView):
    model = Author


class BookInstanceListView(generic.ListView):
    model = BookInstance


class BookInstanceDetailView(generic.DetailView):
    model = BookInstance


class GenreListView(generic.ListView):
    model = Genre
    paginate_by = 10


class GenreDetailView(generic.DetailView):
    model = Genre


class LanguageListView(generic.ListView):
    model = Language
    paginate_by = 10


class LanguageDetailView(generic.DetailView):
    model = Language


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """
    Generic class-based view listing books on loan to current user.
    """

    model = BookInstance
    template_name = "catalog/bookinstance_list_borrowed_user.html"
    paginate_by = 10

    def get_queryset(self):
        return (
            BookInstance.objects.filter(borrower=self.request.user)
            .filter(status__exact="o")
            .order_by("due_back")
        )


class LoanedBooksAllListView(PermissionRequiredMixin, generic.ListView):
    """
    Generic class-based view listing all books on loan. Only visible to librarians.
    """

    permission_required = "catalog.can_mark_returned"
    model = BookInstance
    template_name = "catalog/bookinstance_list_borrowed_all.html"
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact="o").order_by("due_back")


@login_required
@permission_required("catalog.can_mark_returned", raise_exception=True)
def renew_book_librarian(request: HttpRequest, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == "POST":
        form = RenewBookForm(request.POST)
        if form.is_valid():
            book_instance.due_back = form.cleaned_data["renewal_date"]
            book_instance.save()
            return HttpResponseRedirect(reverse("catalog:all-borrowed"))
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={"renewal_date": proposed_renewal_date})

    context = {"form": form, "book_instance": book_instance}

    return render(request, "catalog/book_renew_librarian.html", context=context)


class AuthorCreate(PermissionRequiredMixin, CreateView):
    model = Author
    fields = ["first_name", "last_name", "date_of_birth", "date_of_death"]
    initial = {"date_of_death": "11/11/2023"}
    permission_required = "catalog.add_author"


class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    model = Author
    fields = "__all__"
    permission_required = "catalog.change_author"


class AuthorDelete(PermissionRequiredMixin, DeleteView):
    model = Author
    permission_required = "catalog.delete_author"

    def form_valid(self, form):
        try:
            self.get_object().delete()
            return HttpResponseRedirect(reverse_lazy("catalog:authors"))
        except Exception as e:
            return HttpResponseRedirect(
                reverse("catalog:author-delete", kwargs={"pk": self.get_object().pk})
            )


class BookCreate(PermissionRequiredMixin, CreateView):
    model = Book
    fields = ["title", "author", "summary", "isbn", "genre", "language"]
    permission_required = "catalog.add_book"


class BookUpdate(PermissionRequiredMixin, UpdateView):
    model = Book
    fields = ["title", "author", "summary", "isbn", "genre", "language"]
    permission_required = "catalog.change_book"


class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy("catalog:books")
    permission_required = "catalog.delete_book"

    def form_valid(self, form):
        try:
            self.get_object().delete()
            return HttpResponseRedirect(self.success_url)
        except Exception as e:
            return HttpResponseRedirect(
                reverse("catalog:book-delete", kwargs={"pk": self.get_object().pk})
            )


class GenreCreate(PermissionRequiredMixin, CreateView):
    model = Genre
    fields = ["name"]
    permission_required = "catalog.add_genre"


class GenreUpdate(PermissionRequiredMixin, UpdateView):
    model = Genre
    fields = ["name"]
    permission_required = "catalog.change_genre"


class GenreDelete(PermissionRequiredMixin, DeleteView):
    model = Genre
    permission_required = "catalog.delete_genre"
    success_url = reverse_lazy("catalog:genres")


class LanguageCreate(PermissionRequiredMixin, CreateView):
    model = Language
    fields = ["name"]
    permission_required = "catalog.add_language"
    success_url = reverse_lazy("catalog:languages")


class LanguageUpdate(PermissionRequiredMixin, UpdateView):
    model = Language
    fields = ["name"]
    permission_required = "catalog.change_language"
    success_url = reverse_lazy("catalog:languages")


class LanguageDelete(PermissionRequiredMixin, DeleteView):
    model = Language
    permission_required = "catalog.delete_language"
    success_url = reverse_lazy("catalog:languages")


class BookInstanceCreate(PermissionRequiredMixin, CreateView):
    model = BookInstance
    fields = ["book", "imprint", "due_back", "borrower", "status"]
    permission_required = "catalog.add_bookinstance"
    success_url = reverse_lazy("catalog:bookinstance")


class BookInstanceUpdate(PermissionRequiredMixin, UpdateView):
    model = BookInstance
    fields = ["imprint", "due_back", "borrower", "status"]
    permission_required = "catalog.change_bookinstance"
    success_url = reverse_lazy("catalog:bookinstance")


class BookInstanceDelete(PermissionRequiredMixin, DeleteView):
    model = BookInstance
    permission_required = "catalog.delete_bookinstance"
    success_url = reverse_lazy("catalog:bookinstance")
