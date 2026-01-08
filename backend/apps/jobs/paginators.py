# apps/core/paginators.py
from rest_framework.pagination import PageNumberPagination

class JobPaginator(PageNumberPagination):
    page_size = 20