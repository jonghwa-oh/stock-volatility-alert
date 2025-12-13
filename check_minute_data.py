from database import StockDatabase

db = StockDatabase()
conn = db.connect()
cursor = conn.cursor()

# 12/12 ~ 12/13 데이터 확인
cursor.execute('''
    SELECT date(datetime) as dt, 
           MIN(time(datetime)) as start_time,
           MAX(time(datetime)) as end_time,
           COUNT(*) as cnt,
           MIN(price) as min_price,
           MAX(price) as max_price
    FROM minute_prices 
    WHERE ticker = 'SOXL' 
    AND datetime >= '2025-12-12'
    GROUP BY date(datetime)
    ORDER BY datetime
''')

print("SOXL 날짜별 분봉 데이터:")
print("-" * 70)
for row in cursor.fetchall():
    print(f"  {row[0]} | {row[1]} ~ {row[2]} | {row[3]}건 | ${row[4]:.2f} ~ ${row[5]:.2f}")

db.close()
