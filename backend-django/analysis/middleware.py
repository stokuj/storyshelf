import ipaddress
from django.http import HttpResponseForbidden

DOCKER_NETWORK = ipaddress.ip_network("172.16.0.0/12")


class InternalEndpointMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/internal/"):
            client_ip = ipaddress.ip_address(request.META.get("REMOTE_ADDR", "0.0.0.0"))
            if client_ip not in DOCKER_NETWORK:
                return HttpResponseForbidden("Internal endpoint")
        return self.get_response(request)
