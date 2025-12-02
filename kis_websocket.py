"""
한국투자증권 WebSocket 클라이언트
실시간 시세 수신
"""
import asyncio
import websockets
import json
import aes256
from kis_auth import KISAuth


class KISWebSocket:
    """한국투자증권 WebSocket 클라이언트"""
    
    # WebSocket URL
    WS_URL = "ws://ops.koreainvestment.com:21000"
    
    def __init__(self):
        self.auth = KISAuth()
        self.approval_key = None
        self.websocket = None
        self.is_connected = False
        self.subscriptions = {}  # {ticker: callback}
        
    async def connect(self):
        """WebSocket 연결"""
        if self.is_connected:
            print("⚠️  이미 연결되어 있습니다.")
            return
        
        try:
            # approval key 발급
            self.approval_key = self.auth.get_websocket_approval_key()
            
            # WebSocket 연결
            print(f"🔌 WebSocket 연결 중... {self.WS_URL}")
            self.websocket = await websockets.connect(
                self.WS_URL,
                ping_interval=20,
                ping_timeout=10
            )
            
            self.is_connected = True
            print("✅ WebSocket 연결 성공!")
            
        except Exception as e:
            print(f"❌ WebSocket 연결 실패: {e}")
            self.is_connected = False
            raise
    
    async def disconnect(self):
        """WebSocket 연결 해제"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            print("✅ WebSocket 연결 해제")
    
    def _encrypt_data(self, data: str) -> str:
        """데이터 암호화 (AES256)"""
        # 한국투자증권 AES256 암호화
        # approval_key를 키로 사용
        encryptor = aes256.AESCipher(self.approval_key)
        return encryptor.encrypt(data)
    
    def _decrypt_data(self, data: str) -> str:
        """데이터 복호화 (AES256)"""
        decryptor = aes256.AESCipher(self.approval_key)
        return decryptor.decrypt(data)
    
    async def subscribe_price(self, ticker: str, callback):
        """
        실시간 체결가 구독
        
        Args:
            ticker: 종목코드 (6자리)
            callback: 가격 수신 시 호출될 콜백 함수
        """
        if not self.is_connected:
            await self.connect()
        
        # 구독 요청 메시지
        subscribe_msg = {
            "header": {
                "approval_key": self.approval_key,
                "custtype": "P",
                "tr_type": "1",  # 등록
                "content-type": "utf-8"
            },
            "body": {
                "input": {
                    "tr_id": "H0STCNT0",  # 실시간 체결가
                    "tr_key": ticker
                }
            }
        }
        
        try:
            # 구독 요청 전송
            await self.websocket.send(json.dumps(subscribe_msg))
            self.subscriptions[ticker] = callback
            print(f"📊 {ticker} 실시간 시세 구독 시작")
            
        except Exception as e:
            print(f"❌ {ticker} 구독 실패: {e}")
            raise
    
    async def unsubscribe_price(self, ticker: str):
        """
        실시간 체결가 구독 해제
        
        Args:
            ticker: 종목코드 (6자리)
        """
        if ticker not in self.subscriptions:
            return
        
        # 구독 해제 메시지
        unsubscribe_msg = {
            "header": {
                "approval_key": self.approval_key,
                "custtype": "P",
                "tr_type": "2",  # 해제
                "content-type": "utf-8"
            },
            "body": {
                "input": {
                    "tr_id": "H0STCNT0",
                    "tr_key": ticker
                }
            }
        }
        
        try:
            await self.websocket.send(json.dumps(unsubscribe_msg))
            del self.subscriptions[ticker]
            print(f"📊 {ticker} 실시간 시세 구독 해제")
            
        except Exception as e:
            print(f"❌ {ticker} 구독 해제 실패: {e}")
    
    async def listen(self):
        """
        실시간 데이터 수신 및 처리
        """
        if not self.is_connected:
            await self.connect()
        
        print("👂 실시간 데이터 수신 대기 중...")
        
        try:
            async for message in self.websocket:
                try:
                    # 데이터 파싱
                    if isinstance(message, bytes):
                        message = message.decode('utf-8')
                    
                    data = json.loads(message)
                    
                    # 데이터 타입 확인
                    if 'header' in data and 'body' in data:
                        tr_id = data['header'].get('tr_id')
                        
                        if tr_id == 'H0STCNT0':  # 실시간 체결가
                            await self._handle_price_data(data)
                    
                except json.JSONDecodeError:
                    # 암호화된 데이터인 경우
                    try:
                        decrypted = self._decrypt_data(message)
                        data = json.loads(decrypted)
                        
                        if 'header' in data and 'body' in data:
                            tr_id = data['header'].get('tr_id')
                            
                            if tr_id == 'H0STCNT0':
                                await self._handle_price_data(data)
                    except:
                        pass
                
                except Exception as e:
                    print(f"⚠️  메시지 처리 오류: {e}")
                    continue
        
        except websockets.exceptions.ConnectionClosed:
            print("⚠️  WebSocket 연결이 종료되었습니다.")
            self.is_connected = False
        except Exception as e:
            print(f"❌ 데이터 수신 오류: {e}")
            self.is_connected = False
    
    async def _handle_price_data(self, data: dict):
        """
        실시간 체결가 데이터 처리
        
        Args:
            data: 수신된 데이터
        """
        try:
            body = data.get('body', {})
            output = body.get('output', {})
            
            ticker = output.get('MKSC_SHRN_ISCD', '')  # 종목코드
            current_price = float(output.get('STCK_PRPR', 0))  # 현재가
            
            if ticker in self.subscriptions:
                callback = self.subscriptions[ticker]
                
                # 가격 정보 구성
                price_info = {
                    'ticker': ticker,
                    'current_price': current_price,
                    'change_price': float(output.get('PRDY_VRSS', 0)),  # 전일대비
                    'change_rate': float(output.get('PRDY_CTRT', 0)),  # 등락률
                    'volume': int(output.get('ACML_VOL', 0)),  # 누적거래량
                    'timestamp': output.get('STCK_CNTG_HOUR', '')  # 체결시간
                }
                
                # 콜백 호출
                await callback(price_info)
        
        except Exception as e:
            print(f"⚠️  가격 데이터 처리 오류: {e}")
    
    def close(self):
        """리소스 정리"""
        if self.auth:
            self.auth.close()


# AES256 암호화 클래스 (한국투자증권 제공)
class aes256:
    """AES256 암호화/복호화"""
    
    class AESCipher:
        """AES Cipher"""
        
        def __init__(self, key):
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import pad, unpad
            import hashlib
            
            self.key = hashlib.sha256(key.encode()).digest()
            self.AES = AES
            self.pad = pad
            self.unpad = unpad
        
        def encrypt(self, data):
            """암호화"""
            from Crypto.Cipher import AES
            import base64
            
            cipher = AES.new(self.key, AES.MODE_ECB)
            padded_data = self.pad(data.encode(), AES.block_size)
            encrypted = cipher.encrypt(padded_data)
            return base64.b64encode(encrypted).decode()
        
        def decrypt(self, data):
            """복호화"""
            from Crypto.Cipher import AES
            import base64
            
            cipher = AES.new(self.key, AES.MODE_ECB)
            decrypted = cipher.decrypt(base64.b64decode(data))
            return self.unpad(decrypted, AES.block_size).decode()


if __name__ == "__main__":
    """WebSocket 테스트"""
    
    async def price_callback(price_info):
        """가격 수신 콜백"""
        print(f"\n📊 {price_info['ticker']}")
        print(f"   현재가: {price_info['current_price']:,}원")
        print(f"   전일대비: {price_info['change_price']:+,}원 ({price_info['change_rate']:+.2f}%)")
        print(f"   체결시간: {price_info['timestamp']}")
    
    async def main():
        print("\n" + "="*70)
        print("🧪 한국투자증권 WebSocket 테스트")
        print("="*70)
        
        ws = KISWebSocket()
        
        try:
            # 연결
            await ws.connect()
            
            # 삼성전자 구독
            print("\n📊 삼성전자 (005930) 실시간 시세 구독")
            await ws.subscribe_price("005930", price_callback)
            
            # KODEX 레버리지 구독
            print("📊 KODEX 레버리지 (122630) 실시간 시세 구독")
            await ws.subscribe_price("122630", price_callback)
            
            # 데이터 수신 (10초간)
            print("\n👂 10초간 실시간 데이터 수신 중...")
            await asyncio.wait_for(ws.listen(), timeout=10)
            
        except asyncio.TimeoutError:
            print("\n⏱️  테스트 종료 (10초 경과)")
        except Exception as e:
            print(f"\n❌ 오류: {e}")
        finally:
            await ws.disconnect()
            ws.close()
            print("\n" + "="*70)
    
    # 실행
    asyncio.run(main())



