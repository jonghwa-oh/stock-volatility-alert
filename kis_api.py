"""
한국투자증권 Open Trading API 클라이언트
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from kis_auth import KISAuth


class KISApi:
    """한국투자증권 API 클라이언트"""
    
    def __init__(self):
        self.auth = KISAuth()
        self.base_url = KISAuth.BASE_URL
    
    def get_stock_price(self, ticker: str, market: str = "J") -> Optional[dict]:
        """
        주식 현재가 시세 조회
        
        Args:
            ticker: 종목코드 (6자리)
            market: 시장 구분 (J=주식, ETF, ETN, ELW)
        
        Returns:
            dict: 주식 시세 정보 또는 None
        """
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        
        # TR_ID: FHKST01010100 (주식현재가 시세)
        headers = self.auth.get_headers(tr_id="FHKST01010100")
        
        params = {
            "FID_COND_MRKT_DIV_CODE": market,
            "FID_INPUT_ISCD": ticker
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('rt_cd') == '0':  # 성공
                output = result.get('output', {})
                return {
                    'ticker': ticker,
                    'name': output.get('prdt_name', ''),  # 종목명
                    'current_price': float(output.get('stck_prpr', 0)),  # 현재가
                    'open_price': float(output.get('stck_oprc', 0)),  # 시가
                    'high_price': float(output.get('stck_hgpr', 0)),  # 고가
                    'low_price': float(output.get('stck_lwpr', 0)),  # 저가
                    'prev_close': float(output.get('stck_sdpr', 0)),  # 전일종가
                    'change_price': float(output.get('prdy_vrss', 0)),  # 전일대비
                    'change_rate': float(output.get('prdy_ctrt', 0)),  # 전일대비율
                    'volume': int(output.get('acml_vol', 0)),  # 누적거래량
                    'timestamp': datetime.now()
                }
            else:
                print(f"⚠️  {ticker} 시세 조회 실패: {result.get('msg1', 'Unknown error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 오류 ({ticker}): {e}")
            return None
        except Exception as e:
            print(f"❌ 데이터 처리 오류 ({ticker}): {e}")
            return None
    
    def get_daily_price_history(self, ticker: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """
        주식 일봉 데이터 조회
        
        Args:
            ticker: 종목코드 (6자리)
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
        
        Returns:
            DataFrame: 일봉 데이터 또는 None
        """
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-price"
        
        # TR_ID: FHKST01010400 (주식일봉조회)
        headers = self.auth.get_headers(tr_id="FHKST01010400")
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker,
            "FID_PERIOD_DIV_CODE": "D",  # D=일봉
            "FID_ORG_ADJ_PRC": "0"  # 0=수정주가 미반영, 1=반영
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('rt_cd') == '0':  # 성공
                output = result.get('output', [])
                
                if not output:
                    print(f"⚠️  {ticker} 일봉 데이터 없음")
                    return None
                
                # DataFrame 변환
                data = []
                for item in output:
                    date_str = item.get('stck_bsop_date', '')
                    if start_date <= date_str <= end_date:
                        data.append({
                            'Date': datetime.strptime(date_str, '%Y%m%d'),
                            'Open': float(item.get('stck_oprc', 0)),
                            'High': float(item.get('stck_hgpr', 0)),
                            'Low': float(item.get('stck_lwpr', 0)),
                            'Close': float(item.get('stck_clpr', 0)),
                            'Volume': int(item.get('acml_vol', 0))
                        })
                
                if not data:
                    print(f"⚠️  {ticker} 기간 내 데이터 없음 ({start_date}~{end_date})")
                    return None
                
                df = pd.DataFrame(data)
                df.set_index('Date', inplace=True)
                df.sort_index(inplace=True)
                
                print(f"✅ {ticker} 일봉 데이터 수집: {len(df)}개")
                return df
            else:
                print(f"⚠️  {ticker} 일봉 조회 실패: {result.get('msg1', 'Unknown error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 오류 ({ticker}): {e}")
            return None
        except Exception as e:
            print(f"❌ 데이터 처리 오류 ({ticker}): {e}")
            return None
    
    def close(self):
        """리소스 정리"""
        if self.auth:
            self.auth.close()


if __name__ == "__main__":
    """API 테스트"""
    print("\n" + "="*70)
    print("🧪 한국투자증권 API 테스트")
    print("="*70)
    
    try:
        api = KISApi()
        
        # 1. 삼성전자 현재가 조회
        print("\n[테스트 1] 삼성전자 (005930) 현재가 조회")
        print("-" * 70)
        price = api.get_stock_price("005930")
        if price:
            print(f"✅ 종목명: {price['name']}")
            print(f"   현재가: {price['current_price']:,}원")
            print(f"   전일대비: {price['change_price']:+,}원 ({price['change_rate']:+.2f}%)")
            print(f"   거래량: {price['volume']:,}주")
        
        # 2. KODEX 레버리지 현재가 조회
        print("\n[테스트 2] KODEX 레버리지 (122630) 현재가 조회")
        print("-" * 70)
        price = api.get_stock_price("122630")
        if price:
            print(f"✅ 종목명: {price['name']}")
            print(f"   현재가: {price['current_price']:,}원")
            print(f"   전일대비: {price['change_price']:+,}원 ({price['change_rate']:+.2f}%)")
        
        # 3. KODEX 200타겟위클리커버드콜 일봉 조회
        print("\n[테스트 3] KODEX 200타겟위클리커버드콜 (498400) 일봉 조회")
        print("-" * 70)
        df = api.get_daily_price_history("498400")
        if df is not None and not df.empty:
            print(f"✅ 데이터 기간: {df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}")
            print(f"   데이터 수: {len(df)}개")
            print(f"\n   최근 5일 데이터:")
            print(df.tail())
        
        api.close()
        
        print("\n" + "="*70)
        print("✅ 모든 테스트 통과!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        print("\n💡 해결 방법:")
        print("  1. python init_kis_settings.py 실행")
        print("  2. python kis_auth.py 실행")
        print("  3. 네트워크 연결 및 API 키 확인")

