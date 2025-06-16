from django.views.generic import TemplateView


class IndexView(TemplateView):
    """Index page of Test Radar."""

    template_name = 'index.html'
