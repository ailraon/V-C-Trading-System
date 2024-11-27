from django.shortcuts import redirect
from django.urls import reverse

class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 로그인이 필요한 URL 패턴 목록
        protected_urls = ['/dashboard/', '/investment/', '/transfer/']
        
        # 로그인이 필요한 페이지 접근 시 체크
        if any(request.path.startswith(url) for url in protected_urls) and not request.session.get('user_id'):
            return redirect('login')

        response = self.get_response(request)
        
        # 로그아웃 후 캐시 방지를 위한 헤더 설정
        if request.path == reverse('logout'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
        return response