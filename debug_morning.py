#!/usr/bin/env python3
"""
/morning 명령어 디버그 스크립트
"""
from database import StockDatabase
from daily_analysis import analyze_and_generate_charts
from datetime import datetime
from pathlib import Path
import os

print('='*70)
print('🐛 /morning 명령어 디버그')
print('='*70)

# 1. 환경 확인
print('\n📂 현재 디렉토리:', os.getcwd())
print('📂 charts 디렉토리 존재:', Path('charts').exists())

if Path('charts').exists():
    chart_count = len(list(Path('charts').rglob('*.png')))
    print(f'📊 차트 파일 개수: {chart_count}개')
    
    # 오늘 날짜 차트
    today = datetime.now().strftime('%Y-%m-%d')
    today_charts = list(Path('charts').rglob(f'{today}*.png'))
    print(f'📊 오늘({today}) 차트: {len(today_charts)}개')
    for chart in today_charts:
        print(f'   - {chart}')

# 2. DB 확인
print('\n📊 데이터베이스 확인')
db = StockDatabase()

users = db.get_all_users()
print(f'👤 사용자 수: {len(users)}')

for user in users:
    print(f'\n👤 {user["name"]}:')
    watchlist = db.get_user_watchlist_with_names(user['name'])
    print(f'   관심 종목: {len(watchlist)}개')
    for stock in watchlist:
        print(f'      - {stock["ticker"]}: {stock["name"]}')

# 일봉 데이터 확인
conn = db.connect()
cursor = conn.cursor()
cursor.execute('SELECT ticker, COUNT(*) FROM daily_prices GROUP BY ticker')
data_counts = cursor.fetchall()
print(f'\n📈 일봉 데이터:')
for ticker, count in data_counts:
    print(f'   {ticker}: {count}개')

# 3. 분석 실행
print('\n' + '='*70)
print('📊 분석 실행')
print('='*70)

try:
    analysis_results = analyze_and_generate_charts()
    
    print(f'\n✅ 분석 완료: {len(analysis_results)}개 종목')
    
    for ticker, result in analysis_results.items():
        print(f'\n[{ticker}]')
        print(f'   이름: {result.get("name", "N/A")}')
        print(f'   차트: {result.get("chart_path", "N/A")}')
        
        chart_path = Path(result.get("chart_path", ""))
        print(f'   차트 존재: {chart_path.exists()}')
        
        if result.get('data'):
            data = result['data']
            print(f'   현재가: {data.get("current_price", "N/A")}')
            print(f'   1차 목표: {data.get("target_1x", "N/A")}')

except Exception as e:
    print(f'\n❌ 분석 실패: {e}')
    import traceback
    traceback.print_exc()

# 4. /morning 로직 시뮬레이션
print('\n' + '='*70)
print('🤖 /morning 로직 시뮬레이션')
print('='*70)

user = users[0]
watchlist = db.get_user_watchlist_with_names(user['name'])

if not analysis_results:
    print('❌ 분석 결과가 없습니다.')
elif not watchlist:
    print('❌ 관심 종목이 없습니다.')
else:
    sent_count = 0
    
    for stock in watchlist:
        ticker = stock['ticker']
        result = analysis_results.get(ticker)
        
        if not result:
            print(f'   ❌ {ticker}: 분석 결과 없음')
            continue
        
        chart_path = Path(result['chart_path'])
        if not chart_path.exists():
            print(f'   ❌ {ticker}: 차트 없음 ({chart_path})')
            continue
        
        print(f'   ✅ {ticker}: 전송 가능')
        sent_count += 1
    
    print(f'\n📊 최종 결과: {sent_count}개 종목')
    
    if sent_count == 0:
        print('⚠️ 전송할 차트가 없습니다.')
    else:
        print(f'✅ {sent_count}개 종목 전송 가능')

db.close()

print('\n' + '='*70)
print('✅ 디버그 완료')
print('='*70)

