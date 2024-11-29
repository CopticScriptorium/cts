from texts.models import TextMeta


class SearchField:
    def __init__(self, title):
        self.title = title
        self.values = (
            TextMeta.objects.filter(name=title)
            .values_list("value", flat=True)
            .distinct()
            .order_by("value")
        )
