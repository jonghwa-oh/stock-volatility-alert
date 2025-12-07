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
        country = request.form.get('country', 'US')
        
        if not ticker:
            flash('종목 코드를 입력해주세요.', 'error')
            return render_template('stocks/add.html', username=username)
        
        db = StockDatabase()
        
        # 종목 추가
        user = db.get_user(username)
        if user:
            try:
                cursor = db.connect().cursor()
                cursor.execute('''
                    INSERT INTO user_watchlist (user_id, ticker, country)
                    VALUES (?, ?, ?)
                ''', (user['id'], ticker, country))
                db.connect().commit()
                flash(f'{ticker} 종목이 추가되었습니다! ✅', 'success')
            except Exception as e:
                # 이미 존재하면 활성화
                cursor.execute('''
                    UPDATE user_watchlist SET enabled = 1, country = ?
                    WHERE user_id = ? AND ticker = ?
                ''', (country, user['id'], ticker))
                db.connect().commit()
                flash(f'{ticker} 종목이 활성화되었습니다! ✅', 'success')
        
        db.close()
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
    username = session.get('user')
    
    # 차트 파일 찾기
    charts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'charts', ticker)
    chart_files = []
    
    if os.path.exists(charts_dir):
        files = [f for f in os.listdir(charts_dir) if f.endswith('.png')]
        files.sort(reverse=True)
        chart_files = [f"{ticker}/{f}" for f in files[:5]]  # 최근 5개
    
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
    
    return render_template('stocks/chart.html',
                          username=username,
                          ticker=ticker,
                          stock_info=stock_info,
                          analysis=analysis,
                          chart_files=chart_files)

