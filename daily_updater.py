#!/usr/bin/env python3
"""
매일 자동 스케줄러
- 08:00: 일봉 데이터 업데이트 + 놓친 알림 요약 (월-금)
- 08:50: 오늘의 매수 전략 분석 (월-금)
※ 토/일요일은 모든 알림 및 모니터링 제외
"""
import schedule
import time
from datetime import datetime
from data_collector import DataCollector
from missed_alerts import send_missed_alerts_summary
from daily_analysis import send_daily_alerts
from log_utils import log, log_section, log_success, log_error, log_warning


def is_weekday() -> bool:
    """평일(월-금) 여부 확인"""
    return datetime.now().weekday() < 5  # 0=월, 4=금, 5=토, 6=일


def morning_update_job():
    """일봉 데이터 업데이트 + 놓친 알림 전송 (월-금 08:00)"""
    # 주말 체크
    if not is_weekday():
        log_warning("📅 주말입니다. 아침 업데이트를 건너뜁니다.")
        return
    
    log_section("⏰ 아침 업데이트 시작")
    
    # 1. 일봉 데이터 업데이트
    try:
        log("")
        log("[1/2] 일봉 데이터 업데이트...")
        dc = DataCollector()
        dc.update_daily_data()
        dc.close()
        log_success("일봉 데이터 업데이트 완료!")
    except Exception as e:
        log_error(f"일봉 데이터 업데이트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. 밤 사이 놓친 알림 요약 전송
    try:
        log("")
        log("[2/2] 밤 사이 놓친 알림 확인...")
        send_missed_alerts_summary()
    except Exception as e:
        log_error(f"놓친 알림 전송 실패: {e}")
        import traceback
        traceback.print_exc()
    
    log("")
    log("="*70)
    log_success("아침 업데이트 완료!")
    log("="*70)


def daily_analysis_job():
    """오늘의 매수 전략 분석 (월-금 08:50)"""
    # 주말 체크
    if not is_weekday():
        log_warning("📅 주말입니다. 매수 전략 분석을 건너뜁니다.")
        return
    
    log_section("📊 오늘의 매수 전략 분석 시작")
    
    try:
        # 1. 분석 실행
        from daily_analysis import analyze_and_generate_charts
        log("🔍 차트 생성 및 분석 중...")
        analysis_results = analyze_and_generate_charts()
        
        if not analysis_results:
            log_error("분석 결과가 없습니다.")
            return
        
        log_success(f"분석 완료: {len(analysis_results)}개 종목")
        
        # 2. 사용자별 알림 전송
        send_daily_alerts(analysis_results)
        
    except Exception as e:
        log_error(f"일일 분석 실패: {e}")
        import traceback
        traceback.print_exc()
    
    log("")
    log("="*70)
    log_success("일일 분석 완료!")
    log("="*70)


def main():
    """스케줄러 메인"""
    log_section("📅 일일 스케줄러 시작")
    log("⏰ 스케줄:")
    log("   - 매일 08:00: 일봉 업데이트 + 놓친 알림")
    log("   - 매일 08:50: 매수 전략 분석 (월-금)")
    log("💡 Ctrl+C로 종료")
    log("="*70)
    log("")
    
    # 스케줄 등록
    log("🔧 스케줄 등록 중...")
    schedule.every().day.at("08:00").do(morning_update_job)
    schedule.every().day.at("08:50").do(daily_analysis_job)
    log_success("스케줄 등록 완료:")
    log(f"   - 다음 08:00 실행: {schedule.next_run()}")
    
    # 시작 시 데이터 확인만 (알림 X)
    log("")
    log("🔍 시작 시 데이터 상태 확인...")
    try:
        dc = DataCollector()
        dc.update_daily_data()
        dc.close()
        log_success("데이터 확인 완료!")
    except Exception as e:
        log_error(f"데이터 확인 실패: {e}")
    
    log("")
    log_success("스케줄 등록 완료! 다음 실행 대기 중...")
    log("⏰ 다음 08:00 - 데이터 업데이트 + 놓친 알림")
    log("⏰ 다음 08:50 - 아침 매수 전략 알림")
    
    # 무한 루프
    loop_count = 0
    while True:
        schedule.run_pending()
        loop_count += 1
        
        # 10분마다 상태 로그
        if loop_count % 10 == 0:
            log(f"⏰ 스케줄 대기 중... 다음 실행: {schedule.next_run()}")
        
        time.sleep(60)  # 1분마다 체크


if __name__ == "__main__":
    main()
