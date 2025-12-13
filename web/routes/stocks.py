"""
종목 관리 라우트
"""
import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from web.auth import login_required
from database import StockDatabase
from volatility_analysis import analyze_daily_volatility

stocks_bp = Blueprint('stocks', __name__)


@stocks_bp.route('/')
@login_required
def list_stocks():
    """종목 목록"""
    username = session.get('user')
    
    db = StockDatabase()
    watchlist = db.get_user_watchlist_with_names(username)
    db.close()
    
    return render_template('stocks/list.html',
                          username=username,
                          watchlist=watchlist)


@stocks_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_stock():
    """종목 추가"""
    username = session.get('user')
    
    if request.method == 'POST':
        ticker = request.form.get('ticker', '').strip().upper()
        name = request.form.get('name', '').strip()  # 종목명 추가
        country = request.form.get('country', 'US')
        investment_amount_str = request.form.get('investment_amount', '').strip()
        
        # 투자금액 파싱
        investment_amount = None
        if investment_amount_str:
            try:
                investment_amount = float(investment_amount_str)
            except ValueError:
                pass
        
        # 디버깅 로그
        print(f"📝 종목 추가 요청: ticker='{ticker}', name='{name}', country='{country}', investment={investment_amount}, user='{username}'")
        print(f"📝 전체 폼 데이터: {dict(request.form)}")
        
        if not ticker:
            flash('종목 코드를 입력해주세요.', 'error')
            print("❌ 티커가 비어있음!")
            return render_template('stocks/add.html', username=username)
        
        # 이름이 없으면 티커 사용
        if not name:
            name = ticker
        
        db = StockDatabase()
        
        # 종목 추가 (투자금액 포함)
        success = db.add_user_watchlist(username, ticker, name=name, country=country, investment_amount=investment_amount)
        db.close()
        
        if success:
            flash(f'{name}({ticker}) 종목이 추가되었습니다! ✅', 'success')
            
            # 백그라운드에서 분석 및 차트 생성
            try:
                from volatility_analysis import analyze_daily_volatility, visualize_volatility
                print(f"📊 [{ticker}] 초기 분석 및 차트 생성 시작...")
                
                data = analyze_daily_volatility(ticker, name, country=country)
                if data:
                    chart_path = visualize_volatility(data)
                    if chart_path:
                        print(f"✅ [{ticker}] 차트 생성 완료: {chart_path}")
                        flash(f'📈 {name} 차트가 생성되었습니다!', 'info')
                    else:
                        print(f"⚠️ [{ticker}] 차트 생성 실패")
                else:
                    print(f"⚠️ [{ticker}] 분석 데이터 없음")
            except Exception as e:
                print(f"❌ [{ticker}] 초기 분석 오류: {e}")
                import traceback
                traceback.print_exc()
        else:
            flash('종목 추가에 실패했습니다.', 'error')
        
        return redirect(url_for('stocks.list_stocks'))
    
    return render_template('stocks/add.html', username=username)


@stocks_bp.route('/delete/<ticker>', methods=['POST'])
@login_required
def delete_stock(ticker):
    """종목 삭제 (비활성화)"""
    username = session.get('user')
    
    db = StockDatabase()
    success = db.remove_user_watchlist(username, ticker)
    db.close()
    
    if success:
        flash(f'{ticker} 종목이 삭제되었습니다.', 'success')
    else:
        flash('종목 삭제에 실패했습니다.', 'error')
    
    return redirect(url_for('stocks.list_stocks'))


@stocks_bp.route('/chart/<ticker>')
@login_required
def view_chart(ticker):
    """차트 보기"""
    from volatility_analysis import visualize_volatility
    
    username = session.get('user')
    
    # 종목 분석
    db = StockDatabase()
    watchlist = db.get_user_watchlist_with_names(username)
    db.close()
    
    stock_info = next((s for s in watchlist if s['ticker'] == ticker), None)
    
    analysis = None
    if stock_info:
        try:
            data = analyze_daily_volatility(ticker, stock_info['name'], country=stock_info['country'])
            if data:
                analysis = data
        except Exception as e:
            print(f"분석 오류 ({ticker}): {e}")
    
    # 차트 파일 찾기
    charts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'charts', ticker)
    chart_files = []
    
    if os.path.exists(charts_dir):
        files = [f for f in os.listdir(charts_dir) if f.endswith('.png')]
        files.sort(reverse=True)
        chart_files = [f"{ticker}/{f}" for f in files[:5]]  # 최근 5개
    
    # 차트가 없으면 실시간 생성
    if not chart_files and analysis:
        try:
            print(f"📊 [{ticker}] 차트가 없어서 실시간 생성 중...")
            chart_path = visualize_volatility(analysis)
            if chart_path:
                # 새로 생성된 차트 파일 추가
                chart_filename = os.path.basename(chart_path)
                chart_files = [f"{ticker}/{chart_filename}"]
                print(f"✅ [{ticker}] 차트 생성 완료: {chart_path}")
        except Exception as e:
            print(f"❌ [{ticker}] 차트 생성 실패: {e}")
            import traceback
            traceback.print_exc()
    
    return render_template('stocks/chart.html',
                          username=username,
                          ticker=ticker,
                          stock_info=stock_info,
                          analysis=analysis,
                          chart_files=chart_files)

