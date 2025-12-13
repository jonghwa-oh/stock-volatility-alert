"""
REST API 라우트
"""
from datetime import datetime
from flask import Blueprint, jsonify, request, session
from web.auth import login_required
from database import StockDatabase
from volatility_analysis import analyze_daily_volatility
import FinanceDataReader as fdr

api_bp = Blueprint('api', __name__)

# 종목 리스트 캐시
_kr_stock_list = None
_us_stock_list = None

def get_kr_stock_list():
    """한국 주식 종목 리스트 조회 (캐시)"""
    global _kr_stock_list
    if _kr_stock_list is None:
        try:
            print("📥 한국 종목 리스트 로딩 중...")
            # KOSPI + KOSDAQ + ETF
            kospi = fdr.StockListing('KOSPI')
            kosdaq = fdr.StockListing('KOSDAQ')
            etf = fdr.StockListing('ETF/KR')
            
            _kr_stock_list = []
            
            for _, row in kospi.iterrows():
                _kr_stock_list.append({
                    'ticker': row.get('Code', row.get('Symbol', '')),
                    'name': row.get('Name', ''),
                    'market': 'KOSPI'
                })
            
            for _, row in kosdaq.iterrows():
                _kr_stock_list.append({
                    'ticker': row.get('Code', row.get('Symbol', '')),
                    'name': row.get('Name', ''),
                    'market': 'KOSDAQ'
                })
            
            for _, row in etf.iterrows():
                _kr_stock_list.append({
                    'ticker': row.get('Code', row.get('Symbol', '')),
                    'name': row.get('Name', ''),
                    'market': 'ETF'
                })
            
            print(f"✅ 한국 종목 {len(_kr_stock_list)}개 로드됨")
        except Exception as e:
            print(f"❌ 한국 종목 리스트 로드 실패: {e}")
            _kr_stock_list = []
    
    return _kr_stock_list

def get_us_stock_list():
    """미국 주식 종목 리스트 조회 (캐시)"""
    global _us_stock_list
    if _us_stock_list is None:
        try:
            print("📥 미국 종목 리스트 로딩 중...")
            # NASDAQ + NYSE + ETF
            nasdaq = fdr.StockListing('NASDAQ')
            nyse = fdr.StockListing('NYSE')
            
            _us_stock_list = []
            
            for _, row in nasdaq.iterrows():
                _us_stock_list.append({
                    'ticker': row.get('Symbol', ''),
                    'name': row.get('Name', ''),
                    'market': 'NASDAQ'
                })
            
            for _, row in nyse.iterrows():
                _us_stock_list.append({
                    'ticker': row.get('Symbol', ''),
                    'name': row.get('Name', ''),
                    'market': 'NYSE'
                })
            
            print(f"✅ 미국 종목 {len(_us_stock_list)}개 로드됨")
        except Exception as e:
            print(f"❌ 미국 종목 리스트 로드 실패: {e}")
            _us_stock_list = []
    
    return _us_stock_list


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
                    'std_return': data['std_return'],
                    'volatility': data['std_return']  # 이미 퍼센트 값
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


@api_bp.route('/search/stocks')
@login_required
def search_stocks():
    """
    종목 검색 API
    
    Query params:
        q: 검색어 (종목명 또는 티커)
        country: KR 또는 US (기본값: KR)
        limit: 결과 수 (기본값: 10)
    """
    query = request.args.get('q', '').strip()
    country = request.args.get('country', 'KR').upper()
    limit = request.args.get('limit', 10, type=int)
    
    if len(query) < 1:
        return jsonify({
            'success': True,
            'data': []
        })
    
    query_lower = query.lower()
    results = []
    
    if country == 'KR':
        stock_list = get_kr_stock_list()
    else:
        stock_list = get_us_stock_list()
    
    for stock in stock_list:
        ticker = stock.get('ticker', '')
        name = stock.get('name', '')
        market = stock.get('market', '')
        
        # 이름 또는 티커로 검색 (대소문자 무시)
        if query_lower in name.lower() or query_lower in ticker.lower():
            results.append({
                'ticker': ticker,
                'name': name,
                'market': market,
                'country': country
            })
            
            if len(results) >= limit:
                break
    
    return jsonify({
        'success': True,
        'data': results,
        'query': query,
        'country': country
    })


@api_bp.route('/settings/ntfy', methods=['POST'])
@login_required
def save_ntfy_settings():
    """ntfy 설정 저장 API (사용자별)"""
    username = session.get('user')
    data = request.json
    topic = data.get('topic', '')
    
    db = StockDatabase()
    
    try:
        # 사용자별 ntfy 토픽 저장
        if topic:
            db.set_user_ntfy_topic(username, topic)
        db.close()
        
        return jsonify({
            'success': True,
            'message': '설정이 저장되었습니다.'
        })
    except Exception as e:
        db.close()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/settings/ntfy/test', methods=['POST'])
@login_required
def test_ntfy():
    """ntfy 테스트 알림 전송"""
    data = request.json
    topic = data.get('topic', '')
    
    if not topic:
        return jsonify({
            'success': False,
            'error': '토픽을 입력해주세요.'
        })
    
    try:
        from ntfy_alert import NtfyAlert
        ntfy = NtfyAlert(topic)
        success = ntfy.test()
        
        if success:
            return jsonify({
                'success': True,
                'message': '테스트 알림이 전송되었습니다.'
            })
        else:
            return jsonify({
                'success': False,
                'error': '알림 전송에 실패했습니다.'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/verify/ticker')
@login_required
def verify_ticker():
    """
    티커 유효성 검증 API (KIS API 사용)
    
    Query params:
        ticker: 종목 코드
        country: KR 또는 US
    """
    ticker = request.args.get('ticker', '').strip().upper()
    country = request.args.get('country', 'KR').upper()
    
    if not ticker:
        return jsonify({
            'success': False,
            'valid': False,
            'error': '티커를 입력해주세요.'
        })
    
    try:
        from kis_api import KISApi
        api = KISApi()
        
        if country == 'KR':
            result = api.get_stock_price(ticker)
        else:
            result = api.get_overseas_stock_price_auto(ticker)
        
        api.close()
        
        if result and result.get('current_price', 0) > 0:
            name = result.get('name', ticker)
            
            # KIS API에서 이름이 티커와 같으면 FDR에서 이름 찾기
            if name == ticker:
                if country == 'US':
                    us_stocks = get_us_stock_list()
                    for stock in us_stocks:
                        if stock['ticker'] == ticker:
                            name = stock['name']
                            break
                    
                    # 일반 주식 리스트에서 못 찾으면 ETF 리스트에서 찾기
                    if name == ticker:
                        try:
                            etf_list = fdr.StockListing('ETF/US')
                            matched = etf_list[etf_list['Symbol'] == ticker]
                            if len(matched) > 0:
                                name = matched.iloc[0]['Name']
                        except:
                            pass
                else:  # KR
                    kr_stocks = get_kr_stock_list()
                    for stock in kr_stocks:
                        if stock['ticker'] == ticker:
                            name = stock['name']
                            break
            
            return jsonify({
                'success': True,
                'valid': True,
                'data': {
                    'ticker': ticker,
                    'name': name,
                    'current_price': result.get('current_price', 0),
                    'country': country
                }
            })
        else:
            return jsonify({
                'success': True,
                'valid': False,
                'error': f'{ticker} 종목을 찾을 수 없습니다.'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'valid': False,
            'error': f'검증 오류: {str(e)}'
        })

