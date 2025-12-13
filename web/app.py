"""
Flask 웹 애플리케이션 메인
"""
import os
import sys
from datetime import timedelta

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, redirect, url_for, session, flash, send_from_directory
from web.auth import auth_bp, login_required
from web.routes import main_bp, api_bp, stocks_bp

def create_app():
    """Flask 앱 팩토리"""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # 설정
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'stock-alert-secret-key-2024')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
    
    # 세션 쿠키 설정 (Tailscale IP 호환)
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = False  # HTTP 사용
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_DOMAIN'] = None   # 모든 도메인 허용
    
    # 블루프린트 등록
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(stocks_bp, url_prefix='/stocks')
    
    # 차트 이미지 서빙
    @app.route('/charts/<path:filename>')
    @login_required
    def serve_chart(filename):
        charts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'charts')
        return send_from_directory(charts_dir, filename)
    
    # 에러 핸들러
    @app.errorhandler(404)
    def not_found(e):
        return render_template('error.html', error='페이지를 찾을 수 없습니다.', code=404), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return render_template('error.html', error='서버 오류가 발생했습니다.', code=500), 500
    
    return app


# 개발 서버 실행
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)





