from django.db.models import Avg, Count
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from demo.models import Book
from demo.serializers import BookSerializer


class BookView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug=None):
        if not slug:
            books = Book.objects.filter(is_active=True)
            serializer = BookSerializer(books, many=True)

            count = books.aggregate(total=Count("id"), avg=Avg("id"))
            count_by_name = books.values("name").annotate(count=Count("id"))

            data = {
                "count": count.get("total"),
                "count_by_name": list(count_by_name),
                "books": serializer.data,
            }

            return Response(data)

        book = get_object_or_404(Book, slug=slug, is_active=True)

        serializer = BookSerializer(book)
        return Response(serializer.data)

    def post(self, request):
        serializer = BookSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response(
                {
                    "message": "Book added",
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, slug):
        book = get_object_or_404(Book, slug=slug)
        serializer = BookSerializer(book, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            return Response(
                {"message": "updated successfully", "data": serializer.data}
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, slug):
        book = get_object_or_404(Book, slug=slug)
        book.is_active = False
        book.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
