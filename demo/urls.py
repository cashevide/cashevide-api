from django.urls import path

from .views import BookView

urlpatterns = [
    path("books/", BookView.as_view(), name="books"),
    path("books/<slug:slug>/", BookView.as_view(), name="patch_book"),
]
