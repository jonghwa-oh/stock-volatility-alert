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
    """종목 분석 데이터 조회 (캐시 우선)"""
    db = StockDatabase()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 1. 캐시 확인 (당일 데이터)
    cached = db.get_statistics_cache(ticker, today)
    if cached and cached.get('current_price'):
        # 캐시 데이터 타입 검증 - bytes면 캐시 무효화
        if isinstance(cached.get('current_price'), bytes):
            print(f"  ⚠️ [{ticker}] 캐시 데이터 손상 - 새로 생성")
            cached = None
        else:
            print(f"  📦 [{ticker}] 캐시 사용")
            db.close()
            return {
                'ticker': ticker,
                'name': cached.get('ticker_name') or name,
                'country': cached.get('country') or country,
                'current_price': cached['current_price'],
                'data_date': cached.get('data_date'),
                'target_05x': cached.get('target_05x'),
                'target_1x': cached.get('target_1x'),
                'target_2x': cached.get('target_2x'),
                'drop_05x': cached.get('drop_05x'),
                'drop_1x': cached.get('drop_1x'),
                'drop_2x': cached.get('drop_2x'),
                'std_return': cached.get('std_return'),
                'volatility': cached.get('std_return'),
                'success': True,
                'from_cache': True
            }
    
    # 2. 캐시 없으면 실시간 분석
    try:
        print(f"  📊 [{ticker}] 실시간 분석 중...")
        data = analyze_daily_volatility(ticker, name, country=country)
        if data:
            # 데이터 기준일 포맷팅
            data_date = data.get('data_date')
            if hasattr(data_date, 'strftime'):
                data_date_str = data_date.strftime('%Y-%m-%d')
            else:
                data_date_str = str(data_date)[:10] if data_date else None
            
            # 캐시 저장
            db.update_statistics_cache(
                ticker=ticker,
                date=today,
                ticker_name=name,
                country=country,
                data_date=data_date_str,
                mean_return=data.get('mean_return'),
                std_dev=data['std_return'],
                current_price=data['current_price'],
                target_05sigma=data['target_05x'],
                target_1sigma=data['target_1x'],
                target_2sigma=data['target_2x'],
                drop_05x=data['drop_05x'],
                drop_1x=data['drop_1x'],
                drop_2x=data['drop_2x']
            )
            print(f"  💾 [{ticker}] 캐시 저장 완료")
            
            db.close()
            return {
                'ticker': ticker,
                'name': name,
                'country': country,
                'current_price': data['current_price'],
                'data_date': data_date_str,
                'target_05x': data['target_05x'],
                'target_1x': data['target_1x'],
                'target_2x': data['target_2x'],
                'drop_05x': data['drop_05x'],
                'drop_1x': data['drop_1x'],
                'drop_2x': data['drop_2x'],
                'std_return': data['std_return'],
                'volatility': data['std_return'],
                'success': True
            }
    except Exception as e:
        print(f"분석 오류 ({ticker}): {e}")
        import traceback
        traceback.print_exc()
    
    db.close()
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
    db.close()
    
    # 사용자별 ntfy 토픽 (users 테이블에서)
    ntfy_topic = user.get('ntfy_topic', '') if user else ''
    
    return render_template('settings.html', 
                          username=username,
                          user=user,
                          ntfy_topic=ntfy_topic)

