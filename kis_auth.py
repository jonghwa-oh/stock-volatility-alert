"""
한국투자증권 API 인증 관리
"""
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
from kis_crypto import KISCrypto
from database import StockDatabase


class KISAuth:
    """한국투자증권 API 인증 관리"""
    
    # API 엔드포인트
    BASE_URL = "https://openapi.koreainvestment.com:9443"
    
    def __init__(self):
        self.crypto = KISCrypto()
        self.credentials = self.crypto.load_kis_credentials()
        self.token = None
        self.token_expired = None
        self.db = StockDatabase()
    
    def get_access_token(self, force_refresh=False):
        """
        접근 토큰 발급 또는 캐시된 토큰 반환
        
        Args:
            force_refresh: 강제로 새 토큰 발급
        
        Returns:
            str: 접근 토큰
        """
        # 캐시된 토큰 확인
        if not force_refresh and self._is_token_valid():
            return self.token
        
        # 새 토큰 발급
        url = f"{self.BASE_URL}/oauth2/tokenP"
        
        headers = {
            "content-type": "application/json"
        }
        
        data = {
            "grant_type": "client_credentials",
            "appkey": self.credentials['app_key'],
            "appsecret": self.credentials['app_secret']
        }
        
        try:
            print("🔑 한국투자증권 접근 토큰 발급 중...")
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('access_token'):
                self.token = result['access_token']
                expires_in = int(result.get('expires_in', 86400))  # 기본 24시간
                self.token_expired = datetime.now() + timedelta(seconds=expires_in)
                
                # DB에 저장
                self.db.save_setting('kis_access_token', self.token, 'KIS 접근 토큰')
                self.db.save_setting('kis_token_expired', self.token_expired.isoformat(), '토큰 만료 시간')
                
                print(f"✅ 토큰 발급 성공! (만료: {self.token_expired.strftime('%Y-%m-%d %H:%M:%S')})")
                return self.token
            else:
                raise Exception(f"토큰 발급 실패: {result}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 오류: {e}")
            if hasattr(e.response, 'text'):
                print(f"   응답: {e.response.text}")
            raise
    
    def _is_token_valid(self):
        """토큰 유효성 확인"""
        if self.token and self.token_expired:
            # 만료 5분 전까지 유효로 간주
            return datetime.now() < (self.token_expired - timedelta(minutes=5))
        
        # DB에서 로드 시도
        cached_token = self.db.get_setting('kis_access_token')
        cached_expired = self.db.get_setting('kis_token_expired')
        
        if cached_token and cached_expired:
            try:
                expired_dt = datetime.fromisoformat(cached_expired)
                if datetime.now() < (expired_dt - timedelta(minutes=5)):
                    self.token = cached_token
                    self.token_expired = expired_dt
                    print(f"✅ 캐시된 토큰 사용 (만료: {expired_dt.strftime('%Y-%m-%d %H:%M:%S')})")
                    return True
            except:
                pass
        
        return False
    
    def get_headers(self, tr_id: str = None, custtype: str = "P"):
        """
        API 요청 헤더 생성
        
        Args:
            tr_id: 거래 ID (TR_ID)
            custtype: 고객 유형 (P=개인, B=법인)
        
        Returns:
            dict: 헤더
        """
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.get_access_token()}",
            "appkey": self.credentials['app_key'],
            "appsecret": self.credentials['app_secret'],
            "custtype": custtype
        }
        
        if tr_id:
            headers["tr_id"] = tr_id
        
        return headers
    
    def get_websocket_approval_key(self):
        """
        WebSocket 접속을 위한 approval key 발급
        
        Returns:
            str: approval key
        """
        url = f"{self.BASE_URL}/oauth2/Approval"
        
        headers = {
            "content-type": "application/json"
        }
        
        data = {
            "grant_type": "client_credentials",
            "appkey": self.credentials['app_key'],
            "secretkey": self.credentials['app_secret']
        }
        
        try:
            # 캐시된 approval key 확인
            cached_key = self.db.get_setting('kis_approval_key')
            cached_expired = self.db.get_setting('kis_approval_expired')
            
            if cached_key and cached_expired:
                try:
                    expired_dt = datetime.fromisoformat(cached_expired)
                    if datetime.now() < (expired_dt - timedelta(minutes=5)):
                        print(f"✅ 캐시된 approval key 사용")
                        return cached_key
                except:
                    pass
            
            print("🔑 WebSocket approval key 발급 중...")
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('approval_key'):
                approval_key = result['approval_key']
                # approval key는 24시간 유효
                expired = datetime.now() + timedelta(hours=24)
                
                # DB에 저장
                self.db.save_setting('kis_approval_key', approval_key, 'WebSocket approval key')
                self.db.save_setting('kis_approval_expired', expired.isoformat(), 'approval key 만료 시간')
                
                print(f"✅ Approval key 발급 성공!")
                return approval_key
            else:
                raise Exception(f"Approval key 발급 실패: {result}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 오류: {e}")
            if hasattr(e.response, 'text'):
                print(f"   응답: {e.response.text}")
            raise
    
    def close(self):
        """리소스 정리"""
        if self.db:
            self.db.close()


if __name__ == "__main__":
    """인증 테스트"""
    print("\n" + "="*70)
    print("🧪 한국투자증권 API 인증 테스트")
    print("="*70)
    
    try:
        auth = KISAuth()
        token = auth.get_access_token()
        
        print(f"\n✅ 인증 성공!")
        print(f"  토큰: {token[:20]}...")
        print(f"  만료: {auth.token_expired.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 헤더 테스트
        headers = auth.get_headers(tr_id="FHKST01010100")
        print(f"\n📝 생성된 헤더:")
        for key, value in headers.items():
            if key in ['authorization', 'appkey', 'appsecret']:
                print(f"  {key}: {str(value)[:20]}...")
            else:
                print(f"  {key}: {value}")
        
        auth.close()
        
        print("\n" + "="*70)
        print("✅ 모든 테스트 통과!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        print("\n💡 해결 방법:")
        print("  1. python init_kis_settings.py 실행")
        print("  2. App Key와 App Secret 확인")
        print("  3. 네트워크 연결 확인")

