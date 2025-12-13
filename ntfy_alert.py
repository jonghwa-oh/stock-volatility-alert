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
                         signal_type: str = "매수",
                         sigma: float = 1.0) -> bool:
        """
        주식 알림 전송
        
        Args:
            ticker: 종목 코드
            name: 종목명
            current_price: 현재가
            target_price: 목표가
            signal_type: 신호 유형 (매수/매도)
            sigma: 시그마 배수
        """
        # 이모지 태그 설정
        if signal_type == "매수":
            tags = ["chart_with_downwards_trend", "money_bag"]
            priority = 4  # 높음
        else:
            tags = ["chart_with_upwards_trend", "moneybag"]
            priority = 3  # 보통
        
        title = f"📊 {name} {signal_type} 신호!"
        
        message = f"""종목: {name} ({ticker})
현재가: ${current_price:,.2f}
목표가: ${target_price:,.2f} ({sigma}σ)
신호: {signal_type}"""
        
        return self.send(
            message=message,
            title=title,
            priority=priority,
            tags=tags
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

