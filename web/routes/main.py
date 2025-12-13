"""
메인 대시보드 라우트
"""
import os
from datetime import datetime
from flask import Blueprint, render_template, session
from web.auth import login_required
from database import StockDatabase
from volatility_analysis import analyze_daily_volatility

main_bp = Blueprint('main', __name__)


def get_stock_analysis(ticker: str, name: str, country: str) -> dict:
    """종목 분석 데이터 조회"""
    try:
        data = analyze_daily_volatility(ticker, name, country=country)
        if data:
            return {
                'ticker': ticker,
                'name': name,
                'country': country,
                'current_price': data['current_price'],
                'target_05x': data['target_05x'],
                'target_1x': data['target_1x'],
                'target_2x': data['target_2x'],
                'drop_05x': data['drop_05x'],
                'drop_1x': data['drop_1x'],
                'drop_2x': data['drop_2x'],
                'std_return': data['std_return'],
                'volatility': data['std_return'],  # 이미 퍼센트 값
                'success': True
            }
    except Exception as e:
        print(f"분석 오류 ({ticker}): {e}")
        import traceback
        traceback.print_exc()
    
    return {
        'ticker': ticker,
        'name': name,
        'country': country,
        'success': False,
        'error': '분석 실패'
    }


def get_chart_path(ticker: str) -> str:
    """최신 차트 경로 조회"""
    charts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'charts', ticker)
    
    if not os.path.exists(charts_dir):
        return None
    
    # 최신 파일 찾기
    files = [f for f in os.listdir(charts_dir) if f.endswith('.png')]
    if not files:
        return None
    
    files.sort(reverse=True)
    return f"{ticker}/{files[0]}"


@main_bp.route('/')
@login_required
def index():
    """대시보드 메인"""
    username = session.get('user')
    
    db = StockDatabase()
    watchlist = db.get_user_watchlist_with_names(username)
    db.close()
    
    # 각 종목 분석
    stocks = []
    for item in watchlist:
        analysis = get_stock_analysis(item['ticker'], item['name'], item['country'])
        analysis['chart_path'] = get_chart_path(item['ticker'])
        stocks.append(analysis)
    
    return render_template('index.html', 
                          username=username,
                          stocks=stocks,
                          now=datetime.now())


@main_bp.route('/settings')
@login_required
def settings():
    """설정 페이지"""
    username = session.get('user')
    
    db = StockDatabase()
    user = db.get_user_by_name(username)
    
    # ntfy 설정 가져오기
    ntfy_topic = db.get_setting('ntfy_topic', '')
    notification_method = db.get_setting('notification_method', 'telegram')
    
    db.close()
    
    return render_template('settings.html', 
                          username=username,
                          user=user,
                          ntfy_topic=ntfy_topic,
                          notification_method=notification_method)

