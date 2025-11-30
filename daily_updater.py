#!/usr/bin/env python3
"""
매일 일봉 데이터 자동 업데이트 + 놓친 알림 요약
매일 오전 8:00에 실행
"""
import schedule
import time
from datetime import datetime
from data_collector import DataCollector
from missed_alerts import send_missed_alerts_summary


def update_job():
    """일봉 데이터 업데이트 + 놓친 알림 전송"""
    print("\n" + "="*70)
    print(f"⏰ 일일 업데이트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 1. 일봉 데이터 업데이트
    try:
        print("\n[1/2] 일봉 데이터 업데이트...")
        dc = DataCollector()
        dc.update_daily_data()
        dc.close()
        print("✅ 일봉 데이터 업데이트 완료!")
    except Exception as e:
        print(f"❌ 일봉 데이터 업데이트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. 밤 사이 놓친 알림 요약 전송
    try:
        print("\n[2/2] 밤 사이 놓친 알림 확인...")
        send_missed_alerts_summary()
    except Exception as e:
        print(f"❌ 놓친 알림 전송 실패: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("✅ 일일 업데이트 완료!")
    print("="*70)


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

