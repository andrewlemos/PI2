import logging

logger = logging.getLogger(__name__)

class DebugSocialAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Log para debug
        if 'socialaccount' in request.path:
            logger.info(f"Social Auth Path: {request.path}")
            logger.info(f"User: {request.user}")
            logger.info(f"Session: {dict(request.session)}")
            
        return response