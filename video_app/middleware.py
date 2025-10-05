class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(f"Path: {request.path}")
        print(f"Session keys: {list(request.session.keys())}")
        print(f"User in session: {request.session.get('user_name', 'Not set')}")
        
        response = self.get_response(request)
        return response