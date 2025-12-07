"""
REST API 라우트
"""
from datetime import datetime
from flask import Blueprint, jsonify, request, session
from web.auth import login_required
from database import StockDatabase
from volatility_analysis import analyze_daily_volatility

api_bp = Blueprint('api', __name__)


@api_bp.route('/stocks')
@login_required
def get_stocks():
    """사용자 종목 목록 API"""
    username = session.get('user')
    
    db = StockDatabase()
    watchlist = db.get_user_watchlist_with_names(username)
    db.close()
    
    return jsonify({
        'success': True,
        'data': watchlist
    })


@api_bp.route('/stocks/<ticker>/analysis')
@login_required
def get_stock_analysis(ticker):
    """종목 분석 API"""
    username = session.get('user')
    
    db = StockDatabase()
    watchlist = db.get_user_watchlist_with_names(username)
    db.close()
    
    stock_info = next((s for s in watchlist if s['ticker'] == ticker), None)
    
    if not stock_info:
        return jsonify({
            'success': False,
            'error': '종목을 찾을 수 없습니다.'
        }), 404
    
    try:
        data = analyze_daily_volatility(ticker, stock_info['name'], country=stock_info['country'])
        if data:
            return jsonify({
                'success': True,
                'data': {
                    'ticker': ticker,
                    'name': stock_info['name'],
                    'country': stock_info['country'],
                    'current_price': data['current_price'],
                    'target_05x': data['target_05x'],
                    'target_1x': data['target_1x'],
                    'target_2x': data['target_2x'],
                    'drop_05x': data['drop_05x'],
                    'drop_1x': data['drop_1x'],
                    'drop_2x': data['drop_2x'],
                    'std_dev': data['std_dev'],
                    'volatility': data['daily_volatility']
                }
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
    return jsonify({
        'success': False,
        'error': '분석 실패'
    }), 500


@api_bp.route('/stocks/<ticker>/price')
@login_required
def get_stock_price(ticker):
    """실시간 가격 API"""
    try:
        from kis_api import KISApi
        
        db = StockDatabase()
        watchlist = db.get_user_watchlist_with_names(session.get('user'))
        db.close()
        
        stock_info = next((s for s in watchlist if s['ticker'] == ticker), None)
        
        if not stock_info:
            return jsonify({'success': False, 'error': '종목 없음'}), 404
        
        api = KISApi()
        
        if stock_info['country'] == 'KR':
            price_data = api.get_stock_price(ticker)
        else:
            price_data = api.get_overseas_stock_price_auto(ticker)
        
        api.close()
        
        if price_data:
            return jsonify({
                'success': True,
                'data': {
                    'ticker': ticker,
                    'name': stock_info['name'],
                    'current_price': price_data.get('current_price', 0),
                    'change': price_data.get('change', 0),
                    'change_rate': price_data.get('change_rate', 0),
                    'timestamp': datetime.now().isoformat()
                }
            })
        
        return jsonify({'success': False, 'error': '가격 조회 실패'}), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/user/notification', methods=['POST'])
@login_required
def toggle_notification():
    """알림 설정 토글 API"""
    username = session.get('user')
    enabled = request.json.get('enabled', True)
    
    db = StockDatabase()
    conn = db.connect()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE users SET notification_enabled = ? WHERE name = ?
        ''', (1 if enabled else 0, username))
        conn.commit()
        db.close()
        
        return jsonify({
            'success': True,
            'notification_enabled': enabled
        })
    except Exception as e:
        db.close()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/alerts/history')
@login_required
def get_alert_history():
    """알림 히스토리 API"""
    username = session.get('user')
    limit = request.args.get('limit', 20, type=int)
    
    db = StockDatabase()
    
    # 사용자의 관심 종목만 필터링
    watchlist = db.get_user_watchlist(username)
    
    conn = db.connect()
    cursor = conn.cursor()
    
    placeholders = ','.join(['?' for _ in watchlist])
    cursor.execute(f'''
        SELECT ticker, ticker_name, country, alert_level, target_price, 
               current_price, drop_rate, alert_time, sent
        FROM alert_history
        WHERE ticker IN ({placeholders})
        ORDER BY alert_time DESC
        LIMIT ?
    ''', (*watchlist, limit))
    
    alerts = []
    for row in cursor.fetchall():
        alerts.append({
            'ticker': row[0],
            'name': row[1],
            'country': row[2],
            'level': row[3],
            'target_price': row[4],
            'current_price': row[5],
            'drop_rate': row[6],
            'time': row[7],
            'sent': bool(row[8])
        })
    
    db.close()
    
    return jsonify({
        'success': True,
        'data': alerts
    })

