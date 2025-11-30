#!/usr/bin/env python3
"""
매일 일봉 데이터 자동 업데이트
매일 오전 8:00에 실행
"""
import schedule
import time
from datetime import datetime
from data_collector import DataCollector


def update_job():
    """일봉 데이터 업데이트 작업"""
    print("\n" + "="*70)
    print(f"⏰ 일일 데이터 업데이트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    try:
        dc = DataCollector()
        dc.update_daily_data()
        dc.close()
        print("✅ 일일 데이터 업데이트 완료!")
    except Exception as e:
        print(f"❌ 일일 데이터 업데이트 실패: {e}")
        import traceback
        traceback.print_exc()


def main():
    """스케줄러 메인"""
    print("\n" + "="*70)
    print("📅 일일 데이터 업데이트 스케줄러 시작")
    print("="*70)
    print("⏰ 스케줄: 매일 오전 08:00")
    print("💡 Ctrl+C로 종료")
    print("="*70 + "\n")
    
    # 스케줄 등록: 매일 오전 8시
    schedule.every().day.at("08:00").do(update_job)
    
    # 시작 시 한 번 실행 (어제 데이터 확인)
    print("🔍 시작 시 데이터 확인...")
    update_job()
    
    # 무한 루프
    while True:
        schedule.run_pending()
        time.sleep(60)  # 1분마다 체크


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏸️  스케줄러 종료")
    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()

