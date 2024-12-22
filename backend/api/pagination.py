from rest_framework.pagination import LimitOffsetPagination


class CustomPagination(LimitOffsetPagination):
    default_limit = 3
    max_limit = 100
