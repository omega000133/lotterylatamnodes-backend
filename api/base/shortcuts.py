from urllib.parse import unquote, unquote_plus

from rest_framework.exceptions import NotFound, ParseError


def _get_queryset(model):
    if hasattr(model, "_default_manager"):
        return model._default_manager.all()
    return model


def get_or_404(model, *args, **kwargs):
    queryset = _get_queryset(model)
    model__name = (
        model.__name__ if isinstance(model, type) else model.__class__.__name__
    )
    if not hasattr(queryset, "get"):
        raise ValueError(
            "El primer argumento de get_or_404 debe ser un modelo, manager, "
            "o un objeto queryset, no {}".format(model__name)
        )
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        response = dict(detail="Object not found {}".format(model__name))
        raise NotFound(response)


def validate_value_or_400(value):
    if value is None:
        response = dict(detail="Must send the param {}".format(value))
        raise ParseError(response)


def sanitizer(urlstring):
    return unquote_plus(unquote(urlstring))
