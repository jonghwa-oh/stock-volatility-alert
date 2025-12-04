"""
일일 변동폭(수익률) 기반 투자 전략 분석
하루에 얼마나 오르고 내리는지의 표준편차를 사용
"""

import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.font_manager as fm
import os
import platform
import subprocess
from pathlib import Path

# 전역 폰트 설정 변수
_FONT_CONFIGURED = False
_FONT_PATH = None

def find_nanum_font_path():
    """시스템에서 나눔 폰트 경로를 찾습니다."""
    # 1. 알려진 경로에서 찾기
    known_paths = [
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
        '/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf',
        '/usr/share/fonts/nanum/NanumGothic.ttf',
        '/usr/share/fonts/opentype/nanum/NanumGothic.ttf',
    ]
    
    for path in known_paths:
        if os.path.exists(path):
            return path
    
    # 2. fc-list 명령어로 찾기
    try:
        result = subprocess.run(
            ['fc-list', ':lang=ko', '-f', '%{file}\n'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if 'nanum' in line.lower() and line.endswith('.ttf'):
                    return line
    except Exception as e:
        print(f"  fc-list 실행 실패: {e}")
    
    # 3. find 명령어로 찾기
    try:
        result = subprocess.run(
            ['find', '/usr/share/fonts', '-name', '*anum*.ttf', '-type', 'f'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')[0]
    except Exception as e:
        print(f"  find 실행 실패: {e}")
    
    return None


def setup_korean_font():
    """운영체제에 맞는 한글 폰트를 설정합니다."""
    global _FONT_CONFIGURED, _FONT_PATH
    
    if _FONT_CONFIGURED and _FONT_PATH:
        return _FONT_PATH
    
    system = platform.system()
    print(f"🔧 폰트 설정 중... (OS: {system})")
    
    # matplotlib 캐시 삭제
    cache_dir = matplotlib.get_cachedir()
    if cache_dir and os.path.exists(cache_dir):
        for f in os.listdir(cache_dir):
            if f.startswith('fontlist'):
                try:
                    os.remove(os.path.join(cache_dir, f))
                    print(f"   캐시 삭제: {f}")
                except:
                    pass
    
    if system == 'Darwin':  # macOS
        plt.rcParams['font.family'] = 'AppleGothic'
        plt.rcParams['axes.unicode_minus'] = False
        _FONT_CONFIGURED = True
        print(f"📝 폰트 설정: AppleGothic (macOS)")
        return None
        
    elif system == 'Windows':
        plt.rcParams['font.family'] = 'Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] = False
        _FONT_CONFIGURED = True
        print(f"📝 폰트 설정: Malgun Gothic (Windows)")
        return None
        
    else:  # Linux (Docker 포함)
        font_path = find_nanum_font_path()
        
        if font_path:
            print(f"   나눔 폰트 발견: {font_path}")
            _FONT_PATH = font_path
            _FONT_CONFIGURED = True
            
            # 폰트 매니저에 등록
            fm.fontManager.addfont(font_path)
            
            # rcParams 설정
            font_prop = fm.FontProperties(fname=font_path)
            font_name = font_prop.get_name()
            plt.rcParams['font.family'] = font_name
            plt.rcParams['axes.unicode_minus'] = False
            print(f"📝 폰트 설정 완료: {font_name}")
            return font_path
        else:
            print("⚠️ 나눔 폰트를 찾지 못했습니다.")
            # 설치된 폰트 목록 출력
            available = [f.name for f in fm.fontManager.ttflist][:20]
            print(f"   사용 가능한 폰트: {available}")
            plt.rcParams['axes.unicode_minus'] = False
            _FONT_CONFIGURED = True
            return None


def get_font_properties():
    """차트용 FontProperties 객체를 반환합니다."""
    global _FONT_PATH
    
    if _FONT_PATH and os.path.exists(_FONT_PATH):
        return fm.FontProperties(fname=_FONT_PATH)
    return None


# 폰트 설정 실행
setup_korean_font()


def get_stock_name_from_api(ticker: str) -> str:
    """KIS API에서 종목명을 가져옵니다."""
    try:
        from kis_api import KISApi
        kis = KISApi()
        
        if ticker.isdigit():  # 한국 주식
            price_data = kis.get_stock_price(ticker)
        else:  # 미국 주식
            price_data = kis.get_overseas_stock_price(ticker)
        
        if price_data and 'name' in price_data and price_data['name']:
            return price_data['name']
    except Exception as e:
        print(f"  ⚠️ KIS API 종목명 조회 실패: {e}")
    
    return ticker


def analyze_daily_volatility(ticker, ticker_name, investment_amount=1000000):
    """
    일일 변동성 분석
    
    Args:
        ticker: 종목 코드
        ticker_name: 종목명
        investment_amount: 투자 금액
    """
    # 국가 판별 (한국: 숫자 티커, 미국: 알파벳 티커)
    is_korean = ticker.isdigit()
    currency = "원" if is_korean else "$"
    
    # 종목명이 티커와 같으면 KIS API에서 조회
    if not ticker_name or ticker_name == ticker:
        ticker_name = get_stock_name_from_api(ticker)
        print(f"📌 종목명 조회: {ticker} → {ticker_name}")
    
    print("="*70)
    print(f"📊 {ticker_name} ({ticker}) 일일 변동성 분석")
    print("="*70)
    
    # 1년치 데이터 가져오기
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    try:
        df = fdr.DataReader(ticker, start_date, end_date)
        close_prices = df['Close']
    except Exception as e:
        print(f"❌ 데이터를 가져올 수 없습니다: {e}")
        return None
    
    # 일일 수익률 계산 (%)
    daily_returns = close_prices.pct_change() * 100  # 퍼센트로 변환
    daily_returns = daily_returns.dropna()  # 첫 번째 NaN 제거
    
    # 통계 계산
    current_price = close_prices.iloc[-1]
    mean_return = daily_returns.mean()
    std_return = daily_returns.std()  # 일일 변동폭의 표준편차
    
    # 최대/최소 일일 변동
    max_gain = daily_returns.max()
    max_loss = daily_returns.min()
    
    # 상승/하락일 통계
    up_days = (daily_returns > 0).sum()
    down_days = (daily_returns < 0).sum()
    flat_days = (daily_returns == 0).sum()
    
    # 현재가 기준 매수 목표가 계산
    # 일일 표준편차만큼 하락 시
    drop_05x = std_return * 0.5  # 예: 1% (테스트용)
    drop_1x = std_return  # 예: 2%
    drop_2x = std_return * 2  # 예: 4%
    
    target_05x = current_price * (1 - drop_05x / 100)
    target_1x = current_price * (1 - drop_1x / 100)
    target_2x = current_price * (1 - drop_2x / 100)
    
    # 결과 출력 (통화 단위 구분)
    # 투자금은 항상 원화로 표시 (DB에 원화로 저장되어 있음)
    if is_korean:
        price_str = f"{current_price:,.0f}{currency}"
        target_05x_str = f"{target_05x:,.0f}{currency}"
        target_1x_str = f"{target_1x:,.0f}{currency}"
        target_2x_str = f"{target_2x:,.0f}{currency}"
    else:
        price_str = f"{currency}{current_price:,.2f}"
        target_05x_str = f"{currency}{target_05x:,.2f}"
        target_1x_str = f"{currency}{target_1x:,.2f}"
        target_2x_str = f"{currency}{target_2x:,.2f}"
    
    # 투자금은 항상 원화
    invest_05x_str = f"{investment_amount * 0.5:,.0f}원"  # 0.5배
    invest_1x_str = f"{investment_amount:,.0f}원"
    invest_2x_str = f"{investment_amount * 2:,.0f}원"
    
    print(f"\n📈 1년간 일일 변동 분석:")
    print(f"  • 분석 기간: {len(daily_returns)}일")
    print(f"  • 현재가: {price_str}")
    print(f"  • 상승일: {up_days}일 ({up_days/len(daily_returns)*100:.1f}%)")
    print(f"  • 하락일: {down_days}일 ({down_days/len(daily_returns)*100:.1f}%)")
    
    print(f"\n📊 일일 변동폭 (수익률 기준):")
    print(f"  • 평균 일일 변동: {mean_return:+.3f}%")
    print(f"  • 표준편차: {std_return:.3f}%")
    print(f"  • 해석: 하루에 평균적으로 ±{std_return:.2f}% 정도 움직입니다")
    print(f"  • 최대 상승: {max_gain:+.2f}%")
    print(f"  • 최대 하락: {max_loss:+.2f}%")
    
    print(f"\n💰 매수 전략 (일일 변동폭 기준):")
    print(f"\n  🧪 테스트 매수 시점 (0.5배):")
    print(f"  ├─ 조건: 하루에 표준편차(0.5배)만큼 하락")
    print(f"  ├─ 하락폭: {drop_05x:.2f}%")
    print(f"  ├─ 목표가: {target_05x_str}")
    print(f"  ├─ 투자금: {invest_05x_str} (0.5배)")
    print(f"  └─ 매수량: {(investment_amount * 0.5) / target_05x:,.2f}주")
    
    print(f"\n  📍 1차 매수 시점:")
    print(f"  ├─ 조건: 하루에 표준편차(1배)만큼 하락")
    print(f"  ├─ 하락폭: {drop_1x:.2f}%")
    print(f"  ├─ 목표가: {target_1x_str}")
    print(f"  ├─ 투자금: {invest_1x_str}")
    print(f"  └─ 매수량: {investment_amount / target_1x:,.2f}주")
    
    print(f"\n  📍 2차 매수 시점:")
    print(f"  ├─ 조건: 하루에 표준편차(2배)만큼 하락")
    print(f"  ├─ 하락폭: {drop_2x:.2f}%")
    print(f"  ├─ 목표가: {target_2x_str}")
    print(f"  ├─ 투자금: {invest_2x_str} (2배)")
    print(f"  └─ 매수량: {(investment_amount * 2) / target_2x:,.2f}주")
    
    # 과거 데이터 검증
    print(f"\n✅ 과거 1년간 실제 발생 빈도:")
    
    # 표준편차 1배 이상 하락한 날
    drop_1x_days = (daily_returns <= -drop_1x).sum()
    drop_2x_days = (daily_returns <= -drop_2x).sum()
    
    print(f"  • {drop_1x:.2f}% 이상 하락: {drop_1x_days}일 ({drop_1x_days/len(daily_returns)*100:.1f}%)")
    print(f"  • {drop_2x:.2f}% 이상 하락: {drop_2x_days}일 ({drop_2x_days/len(daily_returns)*100:.1f}%)")
    
    # 확률 분석
    print(f"\n📊 확률 분석:")
    prob_1x = drop_1x_days / len(daily_returns) * 100
    prob_2x = drop_2x_days / len(daily_returns) * 100
    
    if prob_1x > 15:
        freq_1x = "자주 발생 (매수 기회 많음)"
    elif prob_1x > 5:
        freq_1x = "가끔 발생"
    else:
        freq_1x = "드물게 발생"
    
    if prob_2x > 5:
        freq_2x = "가끔 발생"
    elif prob_2x > 1:
        freq_2x = "드물게 발생"
    else:
        freq_2x = "거의 없음"
    
    print(f"  • 1차 매수 기회: {freq_1x}")
    print(f"  • 2차 매수 기회: {freq_2x}")
    
    print("\n" + "="*70)
    
    # 데이터 반환 (시각화용)
    return {
        'ticker': ticker,
        'ticker_name': ticker_name,
        'close_prices': close_prices,
        'daily_returns': daily_returns,
        'current_price': current_price,
        'mean_return': mean_return,
        'std_return': std_return,
        'max_gain': max_gain,
        'max_loss': max_loss,
        'drop_05x': drop_05x,
        'target_05x': target_05x,
        'target_1x': target_1x,
        'target_2x': target_2x,
        'drop_1x': drop_1x,
        'drop_2x': drop_2x,
        'up_days': up_days,
        'down_days': down_days,
        'investment_amount': investment_amount
    }


def visualize_volatility(data):
    """
    일일 변동성을 시각화합니다.
    
    Args:
        data: analyze_daily_volatility의 반환 데이터
    """
    # 차트 생성 전 폰트 재설정
    font_path = setup_korean_font()
    font_prop = get_font_properties()
    
    close_prices = data['close_prices']
    daily_returns = data['daily_returns']
    current = data['current_price']
    mean_ret = data['mean_return']
    std_ret = data['std_return']
    target_1x = data['target_1x']
    target_2x = data['target_2x']
    ticker_name = data['ticker_name']
    ticker = data['ticker']
    
    # 차트 제목용: 한국 종목은 이름(티커), 미국 종목은 티커 - 이름
    is_korean = ticker.isdigit()
    if is_korean:
        chart_title = f"{ticker_name} ({ticker})"
        currency = "원"
        current_str = f"{current:,.0f}{currency}"
        target_1x_str = f"{target_1x:,.0f}{currency}"
        target_2x_str = f"{target_2x:,.0f}{currency}"
    else:
        chart_title = f"{ticker} - {ticker_name}"
        currency = "$"
        current_str = f"{currency}{current:,.2f}"
        target_1x_str = f"{currency}{target_1x:,.2f}"
        target_2x_str = f"{currency}{target_2x:,.2f}"
    
    # 그래프 생성 (3개)
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12))
    
    # 폰트 적용 (fontproperties 직접 사용)
    if font_prop:
        for ax in [ax1, ax2, ax3]:
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_fontproperties(font_prop)
    
    # 그래프 1: 가격 차트
    ax1.plot(close_prices.index, close_prices.values, 'b-', linewidth=2, label='Close')
    # 현재가 및 목표가 라인
    target_05x = data['target_05x']
    drop_05x = data['drop_05x']
    
    # 통화 단위 결정
    if is_korean:
        target_05x_str = f"{target_05x:,.0f}원"
    else:
        target_05x_str = f"{currency}{target_05x:,.2f}"
    
    # 한글/영문 레이블 (폰트 문제 대비)
    use_korean = font_prop is not None
    
    if use_korean:
        lbl_current = f'현재가: {current_str}'
        lbl_test = f'테스트: {target_05x_str} ({drop_05x:.2f}%↓)'
        lbl_1st = f'1차 목표: {target_1x_str} ({data["drop_1x"]:.2f}%↓)'
        lbl_2nd = f'2차 목표: {target_2x_str} ({data["drop_2x"]:.2f}%↓)'
        lbl_title1 = f'{chart_title} - 1년간 가격 추이'
        lbl_date = '날짜'
        lbl_price = '가격'
        lbl_avg = f'평균: {mean_ret:+.2f}%'
        lbl_std1p = f'+1σ: {std_ret:.2f}%'
        lbl_std1m = f'-1σ: -{std_ret:.2f}%'
        lbl_std2p = f'+2σ: {2*std_ret:.2f}%'
        lbl_std2m = f'-2σ: -{2*std_ret:.2f}%'
        lbl_title2 = f'{chart_title} - 일일 수익률'
        lbl_return = '일일 수익률 (%)'
    else:
        lbl_current = f'Current: {current_str}'
        lbl_test = f'Test: {target_05x_str} ({drop_05x:.2f}%)'
        lbl_1st = f'1st Target: {target_1x_str} ({data["drop_1x"]:.2f}%)'
        lbl_2nd = f'2nd Target: {target_2x_str} ({data["drop_2x"]:.2f}%)'
        lbl_title1 = f'{chart_title} - Price (1Y)'
        lbl_date = 'Date'
        lbl_price = 'Price'
        lbl_avg = f'Avg: {mean_ret:+.2f}%'
        lbl_std1p = f'+1 Std: {std_ret:.2f}%'
        lbl_std1m = f'-1 Std: -{std_ret:.2f}%'
        lbl_std2p = f'+2 Std: {2*std_ret:.2f}%'
        lbl_std2m = f'-2 Std: -{2*std_ret:.2f}%'
        lbl_title2 = f'{chart_title} - Daily Return (%)'
        lbl_return = 'Daily Return (%)'
    
    ax1.axhline(y=current, color='red', linestyle='-', linewidth=2.5, label=lbl_current)
    ax1.axhline(y=target_05x, color='lightblue', linestyle=':', linewidth=2, label=lbl_test)
    ax1.axhline(y=target_1x, color='blue', linestyle='--', linewidth=2, label=lbl_1st)
    ax1.axhline(y=target_2x, color='darkblue', linestyle='--', linewidth=2, label=lbl_2nd)
    
    ax1.set_title(lbl_title1, fontsize=14, fontweight='bold', fontproperties=font_prop)
    ax1.set_xlabel(lbl_date, fontsize=12, fontproperties=font_prop)
    ax1.set_ylabel(lbl_price, fontsize=12, fontproperties=font_prop)
    ax1.legend(loc='best', fontsize=10, prop=font_prop)
    ax1.grid(True, alpha=0.3)
    
    # 그래프 2: 일일 변동률 시계열
    colors = ['red' if x < 0 else 'green' for x in daily_returns]
    ax2.bar(daily_returns.index, daily_returns.values, color=colors, alpha=0.6, width=1)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax2.axhline(y=mean_ret, color='blue', linestyle='--', linewidth=2, label=lbl_avg)
    ax2.axhline(y=std_ret, color='orange', linestyle=':', linewidth=2, label=lbl_std1p)
    ax2.axhline(y=-std_ret, color='orange', linestyle=':', linewidth=2, label=lbl_std1m)
    ax2.axhline(y=2*std_ret, color='purple', linestyle=':', linewidth=1.5, alpha=0.7, label=lbl_std2p)
    ax2.axhline(y=-2*std_ret, color='purple', linestyle=':', linewidth=1.5, alpha=0.7, label=lbl_std2m)
    
    # 표준편차 범위 표시
    lbl_1std_range = '1σ 범위' if use_korean else '1 Std Range'
    lbl_2std_range = '2σ 범위' if use_korean else '2 Std Range'
    ax2.fill_between(daily_returns.index, -std_ret, std_ret, alpha=0.1, color='orange', label=lbl_1std_range)
    ax2.fill_between(daily_returns.index, -2*std_ret, 2*std_ret, alpha=0.05, color='purple', label=lbl_2std_range)
    
    ax2.set_title(lbl_title2, fontsize=14, fontweight='bold', fontproperties=font_prop)
    ax2.set_xlabel(lbl_date, fontsize=12, fontproperties=font_prop)
    ax2.set_ylabel(lbl_return, fontsize=12, fontproperties=font_prop)
    ax2.legend(loc='best', fontsize=9, prop=font_prop)
    ax2.grid(True, alpha=0.3)
    
    # 그래프 3: 일일 변동률 분포 (히스토그램)
    ax3.hist(daily_returns.values, bins=50, alpha=0.7, color='steelblue', edgecolor='black', density=True)
    
    # 정규분포 곡선
    x = np.linspace(daily_returns.min(), daily_returns.max(), 100)
    normal_dist = (1 / (std_ret * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean_ret) / std_ret) ** 2)
    
    if use_korean:
        lbl_normal = '정규분포'
        lbl_zero = '변동없음 (0%)'
        lbl_avg_line = f'평균: {mean_ret:+.2f}%'
        lbl_1std_line = f'-1σ: -{std_ret:.2f}%'
        lbl_2std_line = f'-2σ: -{2*std_ret:.2f}%'
        lbl_title3 = f'{chart_title} - 수익률 분포'
        lbl_xlabel3 = '일일 수익률 (%)'
        lbl_ylabel3 = '빈도'
    else:
        lbl_normal = 'Normal Dist'
        lbl_zero = '0% (No Change)'
        lbl_avg_line = f'Avg: {mean_ret:+.2f}%'
        lbl_1std_line = f'-1 Std: -{std_ret:.2f}%'
        lbl_2std_line = f'-2 Std: -{2*std_ret:.2f}%'
        lbl_title3 = f'{chart_title} - Distribution'
        lbl_xlabel3 = 'Daily Return (%)'
        lbl_ylabel3 = 'Frequency'
    
    ax3.plot(x, normal_dist, 'r-', linewidth=2, label=lbl_normal)
    
    # 기준선
    ax3.axvline(x=0, color='black', linestyle='-', linewidth=2, label=lbl_zero)
    ax3.axvline(x=mean_ret, color='blue', linestyle='--', linewidth=2, label=lbl_avg_line)
    ax3.axvline(x=-std_ret, color='orange', linestyle=':', linewidth=2.5, label=lbl_1std_line)
    ax3.axvline(x=-2*std_ret, color='purple', linestyle=':', linewidth=2.5, label=lbl_2std_line)
    
    ax3.set_title(lbl_title3, fontsize=14, fontweight='bold', fontproperties=font_prop)
    ax3.set_xlabel(lbl_xlabel3, fontsize=12, fontproperties=font_prop)
    ax3.set_ylabel(lbl_ylabel3, fontsize=12, fontproperties=font_prop)
    ax3.legend(loc='best', fontsize=10, prop=font_prop)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 통계 정보 박스
    if use_korean:
        textstr = f'평균: {mean_ret:+.3f}%\n'
        textstr += f'표준편차: {std_ret:.3f}%\n'
        textstr += f'최대 상승: {data["max_gain"]:+.2f}%\n'
        textstr += f'최대 하락: {data["max_loss"]:+.2f}%\n'
        textstr += f'─────────────\n'
        textstr += f'상승일: {data["up_days"]}일\n'
        textstr += f'하락일: {data["down_days"]}일'
    else:
        textstr = f'Avg: {mean_ret:+.3f}%\n'
        textstr += f'Std: {std_ret:.3f}%\n'
        textstr += f'Max Up: {data["max_gain"]:+.2f}%\n'
        textstr += f'Max Down: {data["max_loss"]:+.2f}%\n'
        textstr += f'─────────────\n'
        textstr += f'Up Days: {data["up_days"]}\n'
        textstr += f'Down Days: {data["down_days"]}'
    
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax3.text(0.98, 0.98, textstr, transform=ax3.transAxes, fontsize=10,
            verticalalignment='top', horizontalalignment='right', bbox=props, fontproperties=font_prop)
    
    plt.tight_layout()
    
    # 파일 저장 (날짜 prefix + 종목별 폴더)
    today = datetime.now().strftime('%Y-%m-%d')
    ticker_folder = Path('charts') / data['ticker']
    ticker_folder.mkdir(parents=True, exist_ok=True)
    
    safe_name = ticker_name.replace(' ', '_').replace('/', '_')
    filename = ticker_folder / f"{today}_{data['ticker']}_{safe_name}_volatility.png"
    
    # 이미 같은 날짜의 차트가 있으면 덮어쓰기 (중복 방지)
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"\n📊 차트가 저장되었습니다: {filename}")
    plt.close()
    
    return str(filename)  # 파일 경로 반환


def main():
    """메인 실행 함수"""
    print("\n" + "="*70)
    print("🎯 일일 변동폭 기반 투자 전략 분석")
    print("="*70)
    print("📝 개념 설명:")
    print("  • 일일 변동폭 = 하루에 몇 % 오르거나 내리는지")
    print("  • 표준편차 = 일일 변동폭이 평균적으로 얼마나 큰지")
    print("  • 표준편차만큼 하락 = 평소보다 큰 하락으로 매수 기회")
    print("="*70)
    
    # 분석할 종목들
    stocks = [
        ('KS200', '코스피200'),
        ('TQQQ', 'ProShares UltraPro QQQ'),
        ('QLD', 'ProShares Ultra QQQ'),
        ('SOXL', 'Direxion Daily Semiconductor Bull 3X'),
        ('SPY', 'S&P 500 ETF'),
        ('QQQ', 'Invesco QQQ Trust'),
    ]
    
    # 투자 금액
    investment_amount = 1000000  # 100만원
    
    print(f"\n💵 기본 투자 금액: {investment_amount:,}원")
    print(f"📊 분석 종목: {len(stocks)}개\n")
    
    # 각 종목 분석 및 차트 생성
    results = []
    for ticker, name in stocks:
        result = analyze_daily_volatility(ticker, name, investment_amount)
        if result:
            results.append(result)
            # 모든 종목 차트 생성
            print(f"\n📊 {name} 차트 생성 중...")
            visualize_volatility(result)
        print("\n")
    
    # 전체 요약
    print("\n" + "="*70)
    print("📊 전체 종목 일일 변동성 비교")
    print("="*70)
    
    # 변동성 큰 순서로 정렬
    sorted_results = sorted(results, key=lambda x: x['std_return'], reverse=True)
    
    print(f"\n🎯 일일 변동성 순위 (표준편차 기준):\n")
    for idx, data in enumerate(sorted_results, 1):
        print(f"{idx}. {data['ticker_name']}")
        print(f"   • 평균 일일 변동: {data['mean_return']:+.3f}%")
        print(f"   • 표준편차: {data['std_return']:.3f}%")
        print(f"   • 현재가: {data['current_price']:,.2f}")
        print(f"   • 1차 매수가: {data['target_1x']:,.2f} (하루 {data['drop_1x']:.2f}% 하락)")
        print(f"   • 2차 매수가: {data['target_2x']:,.2f} (하루 {data['drop_2x']:.2f}% 하락)")
        print()
    
    print("="*70)
    print("✅ 전체 분석 완료!")
    print(f"📊 모든 종목의 변동성 차트가 저장되었습니다. (총 {len(results)}개)")


if __name__ == "__main__":
    main()

