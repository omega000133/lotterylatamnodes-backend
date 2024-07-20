from rest_framework import viewsets


class ReadOnlyActiveModelViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(activo=True)