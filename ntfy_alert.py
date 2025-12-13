"""
ntfy 푸시 알림 모듈
https://ntfy.sh 또는 셀프호스팅 ntfy 서버 사용
"""
import requests
import json
from typing import Optional


class NtfyAlert:
    """ntfy 푸시 알림 클래스"""
    
    def __init__(self, topic: str, server: str = "https://ntfy.sh"):
        """
        Args:
            topic: ntfy 토픽 이름 (예: stock-alert-jjongz)
            server: ntfy 서버 URL (기본: https://ntfy.sh)
        """
        self.topic = topic
        self.server = server.rstrip('/')
        self.url = f"{self.server}/{self.topic}"
    
    def send(self, 
             message: str, 
             title: Optional[str] = None,
             priority: int = 3,
             tags: Optional[list] = None,
             click_url: Optional[str] = None) -> bool:
        """
        알림 전송 (JSON 방식 - 유니코드/이모지 지원)
        
        Args:
            message: 알림 메시지
            title: 알림 제목 (선택)
            priority: 우선순위 1(최저)~5(최고), 기본 3
            tags: 이모지 태그 리스트 (예: ["chart_with_upwards_trend", "money_bag"])
            click_url: 클릭 시 이동할 URL
        
        Returns:
            성공 여부
        """
        # JSON body 방식 사용 (이모지/유니코드 지원)
        payload = {
            "topic": self.topic,
            "message": message
        }
        
        if title:
            payload["title"] = title
        
        if priority != 3:
            payload["priority"] = priority
        
        if tags:
            payload["tags"] = tags
        
        if click_url:
            payload["click"] = click_url
        
        try:
            response = requests.post(
                self.server,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ ntfy 알림 전송 성공: {title or message[:30]}")
                return True
            else:
                print(f"❌ ntfy 알림 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ ntfy 알림 오류: {e}")
            return False
    
    def send_stock_alert(self, 
                         ticker: str, 
                         name: str,
                         current_price: float,
                         target_price: float,
                         signal_type: str = "1차 매수",
                         sigma: float = 1.0,
                         country: str = 'US',
                         base_url: str = None,
                         investment_amount: float = None,
                         prev_close: float = None) -> bool:
        """
        주식 알림 전송
        
        Args:
            ticker: 종목 코드
            name: 종목명
            current_price: 현재가
            target_price: 목표가
            signal_type: 신호 유형 (1차 매수, 2차 매수 등)
            sigma: 시그마 배수
            country: 국가 코드 (KR/US)
            base_url: 웹 대시보드 기본 URL (예: http://192.168.1.100:8080)
            investment_amount: 투자금액 (한국: 원, 미국: 달러)
            prev_close: 전일 종가
        """
        import os
        import math
        from datetime import datetime
        import pytz
        
        # 이모지 태그 설정
        tags = ["chart_with_downwards_trend", "money_bag"]
        priority = 4  # 높음
        
        # 시그마에 따른 타이틀
        if sigma == 0.5:
            title = f"🧪 {name} 테스트 매수"
        elif sigma == 1.0:
            title = f"📊 {name} 1차 매수"
        else:
            title = f"🔥 {name} 2차 매수"
        
        # 현재 시간 (한국/미국)
        if country == 'KR':
            tz = pytz.timezone('Asia/Seoul')
            time_label = "🇰🇷 한국시간"
        else:
            tz = pytz.timezone('America/New_York')
            time_label = "🇺🇸 미국시간"
        
        now = datetime.now(tz)
        time_str = now.strftime('%H:%M:%S')
        
        # 가격 포맷 함수
        def fmt_price(price, is_kr):
            if is_kr:
                return f"{int(price):,}원"
            else:
                return f"${math.floor(price * 100) / 100:,.2f}"
        
        is_kr = (country == 'KR')
        current_fmt = fmt_price(current_price, is_kr)
        target_fmt = fmt_price(target_price, is_kr)
        
        # 하락률 계산
        if prev_close and prev_close > 0:
            drop_rate = ((prev_close - current_price) / prev_close) * 100
            prev_fmt = fmt_price(prev_close, is_kr)
        else:
            drop_rate = ((target_price - current_price) / target_price) * 100 if target_price > 0 else 0
            prev_fmt = "-"
        
        # 메시지 구성
        message = f"""{time_label} {time_str}

📈 {name} ({ticker})
━━━━━━━━━━━━━━━━
전일종가: {prev_fmt}
현재가: {current_fmt} (▼{abs(drop_rate):.1f}%)
목표가: {target_fmt} ({sigma}σ)"""
        
        # 투자금액이 설정된 경우 매수 수량 계산
        if investment_amount and investment_amount > 0 and current_price > 0:
            shares = int(investment_amount / current_price)
            if is_kr:
                invest_fmt = f"{int(investment_amount):,}원"
            else:
                invest_fmt = f"${investment_amount:,.0f}"
            
            if shares > 0:
                message += f"\n━━━━━━━━━━━━━━━━\n💰 {invest_fmt} → {shares}주 매수"
            else:
                message += f"\n━━━━━━━━━━━━━━━━\n⚠️ {invest_fmt} (1주 미만)"
        
        # 클릭 URL 생성
        click_url = None
        url_base = base_url or os.environ.get('WEB_BASE_URL', '')
        if url_base:
            click_url = f"{url_base.rstrip('/')}/stocks/chart/{ticker}"
        
        return self.send(
            message=message,
            title=title,
            priority=priority,
            tags=tags,
            click_url=click_url
        )
    
    def send_morning_report(self, report: str) -> bool:
        """아침 리포트 전송"""
        return self.send(
            message=report,
            title="📈 오늘의 투자 분석",
            priority=3,
            tags=["sunrise", "chart_with_upwards_trend"]
        )
    
    def test(self) -> bool:
        """테스트 알림 전송"""
        return self.send(
            message="ntfy 알림이 정상적으로 작동합니다! 🎉",
            title="🔔 테스트 알림",
            priority=3,
            tags=["white_check_mark", "bell"]
        )


# 전역 인스턴스 (설정 후 사용)
_ntfy_instance: Optional[NtfyAlert] = None


def init_ntfy(topic: str, server: str = "https://ntfy.sh"):
    """ntfy 초기화"""
    global _ntfy_instance
    _ntfy_instance = NtfyAlert(topic, server)
    return _ntfy_instance


def get_ntfy() -> Optional[NtfyAlert]:
    """ntfy 인스턴스 반환"""
    return _ntfy_instance


def send_ntfy(message: str, title: Optional[str] = None, **kwargs) -> bool:
    """간편 알림 전송"""
    if _ntfy_instance:
        return _ntfy_instance.send(message, title, **kwargs)
    else:
        print("❌ ntfy가 초기화되지 않았습니다. init_ntfy()를 먼저 호출하세요.")
        return False


# 테스트
if __name__ == "__main__":
    # 토픽 이름을 변경하세요!
    ntfy = NtfyAlert("stock-alert-test")
    
    # 테스트 알림
    ntfy.test()
    
    # 주식 알림 테스트
    ntfy.send_stock_alert(
        ticker="TQQQ",
        name="ProShares UltraPro QQQ",
        current_price=45.50,
        target_price=44.00,
        signal_type="매수",
        sigma=1.0
    )

