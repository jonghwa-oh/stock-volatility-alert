"""
인증 관련 모듈
- 로그인/로그아웃
- 세션 관리
- 비밀번호 해싱
- 로그인 실패 제한 (Brute Force 방지)
"""
import hashlib
from functools import wraps
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import StockDatabase

auth_bp = Blueprint('auth', __name__)

# ==========================================
# 로그인 실패 제한 설정
# ==========================================
MAX_LOGIN_ATTEMPTS = 5      # 최대 실패 횟수
LOCKOUT_MINUTES = 10        # 잠금 시간 (분)

# IP별 로그인 실패 기록 {ip: {'count': n, 'locked_until': datetime}}
_login_attempts = {}


def get_client_ip():
    """클라이언트 IP 가져오기"""
    # 프록시/로드밸런서 뒤에 있을 경우
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or 'unknown'


def is_locked_out(ip: str) -> tuple[bool, int]:
    """
    IP가 잠겨있는지 확인
    Returns: (잠금 여부, 남은 시간(초))
    """
    if ip not in _login_attempts:
        return False, 0
    
    attempt = _login_attempts[ip]
    
    if attempt.get('locked_until'):
        now = datetime.now()
        if now < attempt['locked_until']:
            remaining = (attempt['locked_until'] - now).seconds
            return True, remaining
        else:
            # 잠금 해제
            _login_attempts[ip] = {'count': 0, 'locked_until': None}
            return False, 0
    
    return False, 0


def record_failed_attempt(ip: str) -> tuple[int, bool]:
    """
    로그인 실패 기록
    Returns: (실패 횟수, 잠금 여부)
    """
    if ip not in _login_attempts:
        _login_attempts[ip] = {'count': 0, 'locked_until': None}
    
    _login_attempts[ip]['count'] += 1
    count = _login_attempts[ip]['count']
    
    if count >= MAX_LOGIN_ATTEMPTS:
        _login_attempts[ip]['locked_until'] = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
        return count, True
    
    return count, False


def clear_failed_attempts(ip: str):
    """로그인 성공 시 실패 기록 초기화"""
    if ip in _login_attempts:
        del _login_attempts[ip]


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
    
    client_ip = get_client_ip()
    
    # 잠금 상태 확인
    locked, remaining_seconds = is_locked_out(client_ip)
    if locked:
        remaining_min = remaining_seconds // 60 + 1
        flash(f'🔒 로그인이 일시 차단되었습니다. {remaining_min}분 후에 다시 시도해주세요.', 'error')
        return render_template('login.html', locked=True, remaining=remaining_min)
    
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
            count, is_locked = record_failed_attempt(client_ip)
            if is_locked:
                flash(f'🔒 {MAX_LOGIN_ATTEMPTS}회 실패로 {LOCKOUT_MINUTES}분간 로그인이 차단됩니다.', 'error')
            else:
                remaining = MAX_LOGIN_ATTEMPTS - count
                flash(f'존재하지 않는 사용자입니다. (남은 시도: {remaining}회)', 'error')
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
            count, is_locked = record_failed_attempt(client_ip)
            if is_locked:
                flash(f'🔒 {MAX_LOGIN_ATTEMPTS}회 실패로 {LOCKOUT_MINUTES}분간 로그인이 차단됩니다.', 'error')
            else:
                remaining = MAX_LOGIN_ATTEMPTS - count
                flash(f'비밀번호가 일치하지 않습니다. (남은 시도: {remaining}회)', 'error')
            return render_template('login.html')
        
        # 로그인 성공 - 실패 기록 초기화
        clear_failed_attempts(client_ip)
        
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


