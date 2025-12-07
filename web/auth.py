"""
인증 관련 모듈
- 로그인/로그아웃
- 세션 관리
- 비밀번호 해싱
"""
import hashlib
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import StockDatabase

auth_bp = Blueprint('auth', __name__)


def hash_password(password: str) -> str:
    """비밀번호 해싱 (SHA-256)"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def login_required(f):
    """로그인 필수 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('로그인이 필요합니다.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """로그인 페이지"""
    if 'user' in session:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('아이디와 비밀번호를 입력해주세요.', 'error')
            return render_template('login.html')
        
        db = StockDatabase()
        user = db.get_user_by_name(username)
        db.close()
        
        if not user:
            flash('존재하지 않는 사용자입니다.', 'error')
            return render_template('login.html')
        
        if not user['enabled']:
            flash('비활성화된 계정입니다.', 'error')
            return render_template('login.html')
        
        # 비밀번호 미설정 시 (첫 로그인)
        if not user['password_hash']:
            # 비밀번호 설정 페이지로 이동
            session['temp_user'] = username
            return redirect(url_for('auth.set_password'))
        
        # 비밀번호 확인
        password_hash = hash_password(password)
        if user['password_hash'] != password_hash:
            flash('비밀번호가 일치하지 않습니다.', 'error')
            return render_template('login.html')
        
        # 로그인 성공
        session['user'] = username
        session['user_id'] = user['id']
        
        if remember:
            session.permanent = True
        
        flash(f'{username}님, 환영합니다! 👋', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('login.html')


@auth_bp.route('/set-password', methods=['GET', 'POST'])
def set_password():
    """비밀번호 설정 (첫 로그인 시)"""
    if 'temp_user' not in session:
        return redirect(url_for('auth.login'))
    
    username = session['temp_user']
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        if len(password) < 4:
            flash('비밀번호는 4자 이상이어야 합니다.', 'error')
            return render_template('set_password.html', username=username)
        
        if password != password_confirm:
            flash('비밀번호가 일치하지 않습니다.', 'error')
            return render_template('set_password.html', username=username)
        
        # 비밀번호 저장
        db = StockDatabase()
        password_hash = hash_password(password)
        success = db.set_user_password(username, password_hash)
        
        if success:
            user = db.get_user_by_name(username)
            db.close()
            
            # 세션 정리 및 로그인 처리
            session.pop('temp_user', None)
            session['user'] = username
            session['user_id'] = user['id']
            session.permanent = True
            
            flash('비밀번호가 설정되었습니다! 🎉', 'success')
            return redirect(url_for('main.index'))
        else:
            db.close()
            flash('비밀번호 설정에 실패했습니다.', 'error')
    
    return render_template('set_password.html', username=username)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """비밀번호 변경"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        new_password_confirm = request.form.get('new_password_confirm', '')
        
        username = session['user']
        db = StockDatabase()
        user = db.get_user_by_name(username)
        
        # 현재 비밀번호 확인
        if user['password_hash'] != hash_password(current_password):
            db.close()
            flash('현재 비밀번호가 일치하지 않습니다.', 'error')
            return render_template('change_password.html')
        
        if len(new_password) < 4:
            db.close()
            flash('새 비밀번호는 4자 이상이어야 합니다.', 'error')
            return render_template('change_password.html')
        
        if new_password != new_password_confirm:
            db.close()
            flash('새 비밀번호가 일치하지 않습니다.', 'error')
            return render_template('change_password.html')
        
        # 비밀번호 변경
        password_hash = hash_password(new_password)
        success = db.set_user_password(username, password_hash)
        db.close()
        
        if success:
            flash('비밀번호가 변경되었습니다! 🔐', 'success')
            return redirect(url_for('main.settings'))
        else:
            flash('비밀번호 변경에 실패했습니다.', 'error')
    
    return render_template('change_password.html')


@auth_bp.route('/logout')
def logout():
    """로그아웃"""
    username = session.get('user', '')
    session.clear()
    flash(f'{username}님, 안녕히 가세요! 👋', 'info')
    return redirect(url_for('auth.login'))

