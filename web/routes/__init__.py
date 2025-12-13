"""
Flask 라우트 모듈
"""
from web.routes.main import main_bp
from web.routes.api import api_bp
from web.routes.stocks import stocks_bp

__all__ = ['main_bp', 'api_bp', 'stocks_bp']





