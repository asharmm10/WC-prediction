"""Middleware for the FIFA World Cup 2026 Family Prediction League."""

from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin


class XTransformPortMiddleware(MiddlewareMixin):
    """
    Middleware that adds XTransformPort query parameter to redirect URLs
    when the original request came through the Caddy gateway with XTransformPort.

    This ensures that after form submissions (login, logout, predictions),
    the redirect URL still includes the XTransformPort parameter so that
    the Caddy gateway routes the request to Django instead of Next.js.
    """

    PARAM = 'XTransformPort'
    PORT = '8000'

    def process_request(self, request):
        # Store whether the request came with XTransformPort
        request.is_behind_gateway = self.PARAM in request.GET

    def process_response(self, request, response):
        # Only modify redirect responses
        if not isinstance(response, HttpResponseRedirect):
            return response

        # Only modify if the original request had XTransformPort
        if not getattr(request, 'is_behind_gateway', False):
            return response

        # Get the redirect URL
        url = response.url
        if not url:
            return response

        # Don't modify external URLs
        if url.startswith('http') and '://127.0.0.1' not in url and '://localhost' not in url:
            return response

        # Add XTransformPort to the redirect URL
        if self.PARAM not in url:
            separator = '&' if '?' in url else '?'
            url = f"{url}{separator}{self.PARAM}={self.PORT}"
            response.url = url
            response['Location'] = url

        return response
