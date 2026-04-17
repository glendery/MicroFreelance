from .models import ActivityLog

class ActivityLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Proses request
        response = self.get_response(request)

        # Log aktivitas jika user sudah login dan bukan akses static/media/admin
        if request.user.is_authenticated and not request.path.startswith(('/static/', '/media/', '/admin/')):
            action = f"Accessed {request.path} via {request.method}"
            ActivityLog.objects.create(
                user=request.user,
                action=action,
                ip_address=self.get_client_ip(request)
            )

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
