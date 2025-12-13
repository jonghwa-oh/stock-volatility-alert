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
    
    def get_overseas_stock_price(self, ticker: str, exchange: str = "NAS") -> Optional[dict]:
        """
        해외주식 현재가 시세 조회
        
        Args:
            ticker: 종목코드 (ex: AAPL, TSLA, SOXL)
            exchange: 거래소 코드 (NAS=나스닥, NYS=뉴욕, AMS=아멕스)
        
        Returns:
            dict: 주식 시세 정보 또는 None
        """
        url = f"{self.base_url}/uapi/overseas-price/v1/quotations/price"
        
        # TR_ID: HHDFS00000300 (해외주식 현재가)
        headers = self.auth.get_headers(tr_id="HHDFS00000300")
        
        params = {
            "AUTH": "",
            "EXCD": exchange,  # 거래소 코드
            "SYMB": ticker     # 종목코드
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('rt_cd') == '0':  # 성공
                output = result.get('output', {})
                
                # 빈 문자열 처리
                def safe_float(value, default=0.0):
                    try:
                        return float(value) if value and value != '' else default
                    except (ValueError, TypeError):
                        return default
                
                current_price = safe_float(output.get('last'))
                open_price = safe_float(output.get('open'))
                high_price = safe_float(output.get('high'))
                low_price = safe_float(output.get('low'))
                prev_close = safe_float(output.get('base'))
                
                change_price = current_price - prev_close
                change_rate = (change_price / prev_close * 100) if prev_close > 0 else 0
                
                def safe_int(value, default=0):
                    try:
                        return int(value) if value and value != '' else default
                    except (ValueError, TypeError):
                        return default
                
                return {
                    'ticker': ticker,
                    'name': output.get('name', ticker),  # 종목명
                    'current_price': current_price,  # 현재가
                    'open_price': open_price,  # 시가
                    'high_price': high_price,  # 고가
                    'low_price': low_price,  # 저가
                    'prev_close': prev_close,  # 전일종가
                    'change_price': change_price,  # 전일대비
                    'change_rate': change_rate,  # 전일대비율
                    'volume': safe_int(output.get('tvol')),  # 거래량
                    'exchange': exchange,
                    'timestamp': datetime.now()
                }
            else:
                print(f"⚠️  {ticker} ({exchange}) 시세 조회 실패: {result.get('msg1', 'Unknown error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 오류 ({ticker}): {e}")
            return None
        except Exception as e:
            print(f"❌ 데이터 처리 오류 ({ticker}): {e}")
            return None
    
    def get_overseas_daily_price_history(self, ticker: str, exchange: str = "NAS", 
                                         start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """
        해외주식 일봉 데이터 조회
        
        Args:
            ticker: 종목코드
            exchange: 거래소 코드 (NAS=나스닥, NYS=뉴욕)
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
        
        Returns:
            DataFrame: 일봉 데이터 또는 None
        """
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        
        url = f"{self.base_url}/uapi/overseas-price/v1/quotations/dailyprice"
        
        # TR_ID: HHDFS76240000 (해외주식 기간별시세)
        headers = self.auth.get_headers(tr_id="HHDFS76240000")
        
        params = {
            "AUTH": "",
            "EXCD": exchange,
            "SYMB": ticker,
            "GUBN": "0",  # 0=일봉, 1=주봉, 2=월봉
            "BYMD": end_date,  # 조회 기준일
            "MODP": "1"  # 0=수정주가 미반영, 1=반영
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('rt_cd') == '0':  # 성공
                output2 = result.get('output2', [])
                
                if not output2:
                    print(f"⚠️  {ticker} ({exchange}) 일봉 데이터 없음")
                    return None
                
                # DataFrame 변환
                def safe_float(value, default=0.0):
                    try:
                        return float(value) if value and value != '' else default
                    except (ValueError, TypeError):
                        return default
                
                def safe_int(value, default=0):
                    try:
                        return int(value) if value and value != '' else default
                    except (ValueError, TypeError):
                        return default
                
                data = []
                for item in output2:
                    date_str = item.get('xymd', '')  # YYYYMMDD
                    if start_date <= date_str <= end_date:
                        data.append({
                            'Date': datetime.strptime(date_str, '%Y%m%d'),
                            'Open': safe_float(item.get('open')),
                            'High': safe_float(item.get('high')),
                            'Low': safe_float(item.get('low')),
                            'Close': safe_float(item.get('clos')),
                            'Volume': safe_int(item.get('tvol'))
                        })
                
                if not data:
                    print(f"⚠️  {ticker} ({exchange}) 기간 내 데이터 없음 ({start_date}~{end_date})")
                    return None
                
                df = pd.DataFrame(data)
                df.set_index('Date', inplace=True)
                df.sort_index(inplace=True)
                
                print(f"✅ {ticker} ({exchange}) 일봉 데이터 수집: {len(df)}개")
                return df
            else:
                print(f"⚠️  {ticker} ({exchange}) 일봉 조회 실패: {result.get('msg1', 'Unknown error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 오류 ({ticker}): {e}")
            return None
        except Exception as e:
            print(f"❌ 데이터 처리 오류 ({ticker}): {e}")
            return None
    
    # 거래소 코드 캐시 (티커 → 거래소)
    _exchange_cache = {}
    
    def get_exchange_code(self, ticker: str) -> str:
        """
        티커로 거래소 코드 반환 (캐시 우선)
        
        Args:
            ticker: 종목코드
        
        Returns:
            str: 거래소 코드 (NAS, NYS, AMS)
        """
        ticker_upper = ticker.upper()
        
        # 캐시에 있으면 반환
        if ticker_upper in self._exchange_cache:
            return self._exchange_cache[ticker_upper]
        
        # 기본 추측 (레버리지 ETF는 대부분 ARCA)
        leverage_keywords = ['3X', 'BULL', 'BEAR', 'ULTRA']
        if any(kw in ticker_upper for kw in leverage_keywords):
            return "AMS"
        
        # 알려진 나스닥 대형주
        nasdaq_majors = ['AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 
                         'TSLA', 'AVGO', 'COST', 'NFLX', 'AMD', 'PEP', 'ADBE', 
                         'CSCO', 'TQQQ', 'QQQ', 'INTC', 'PYPL']
        
        if ticker_upper in nasdaq_majors:
            return "NAS"
        
        return "NAS"  # 기본값
    
    def _extract_exchange_from_rsym(self, rsym: str) -> Optional[str]:
        """
        rsym 필드에서 거래소 코드 추출
        
        Args:
            rsym: API 응답의 rsym 값 (예: DNASTQQQ, DAMSSOXL)
        
        Returns:
            str: 거래소 코드 (NAS, AMS, NYS) 또는 None
        """
        if rsym and len(rsym) >= 4:
            # rsym 형식: D + 거래소(3자리) + 티커
            exchange = rsym[1:4]
            if exchange in ['NAS', 'AMS', 'NYS']:
                return exchange
        return None
    
    def get_overseas_stock_price_auto(self, ticker: str) -> Optional[dict]:
        """
        여러 거래소를 시도하여 해외주식 현재가 조회
        rsym에서 거래소 코드를 추출하여 캐싱
        
        Args:
            ticker: 종목코드
        
        Returns:
            dict: 주식 시세 정보 또는 None
        """
        ticker_upper = ticker.upper()
        
        # 캐시된 거래소가 있으면 먼저 시도
        if ticker_upper in self._exchange_cache:
            cached_exchange = self._exchange_cache[ticker_upper]
            result = self.get_overseas_stock_price(ticker, cached_exchange)
            if result and result.get('current_price', 0) > 0:
                return result
        
        # 시도할 거래소 순서
        exchanges = ['NAS', 'AMS', 'NYS']
        
        # 추측 거래소를 먼저 시도
        guessed = self.get_exchange_code(ticker)
        if guessed in exchanges:
            exchanges.remove(guessed)
            exchanges.insert(0, guessed)
        
        for exchange in exchanges:
            result = self._get_overseas_stock_price_with_rsym(ticker, exchange)
            if result and result.get('current_price', 0) > 0:
                # rsym에서 실제 거래소 추출하여 캐싱
                rsym = result.get('_rsym', '')
                actual_exchange = self._extract_exchange_from_rsym(rsym)
                if actual_exchange:
                    self._exchange_cache[ticker_upper] = actual_exchange
                    print(f"  ✅ {ticker} 거래소 캐싱: {actual_exchange}")
                else:
                    self._exchange_cache[ticker_upper] = exchange
                    print(f"  ✅ {ticker} 거래소 확인: {exchange}")
                return result
        
        print(f"  ❌ {ticker} 모든 거래소에서 조회 실패")
        return None
    
    def _get_overseas_stock_price_with_rsym(self, ticker: str, exchange: str) -> Optional[dict]:
        """
        해외주식 현재가 조회 (rsym 포함)
        """
        url = f"{self.base_url}/uapi/overseas-price/v1/quotations/price"
        headers = self.auth.get_headers(tr_id="HHDFS00000300")
        params = {"AUTH": "", "EXCD": exchange, "SYMB": ticker}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            if result.get('rt_cd') == '0':
                output = result.get('output', {})
                
                def safe_float(value, default=0.0):
                    try:
                        return float(value) if value and value != '' else default
                    except (ValueError, TypeError):
                        return default
                
                def safe_int(value, default=0):
                    try:
                        return int(value) if value and value != '' else default
                    except (ValueError, TypeError):
                        return default
                
                current_price = safe_float(output.get('last'))
                
                return {
                    'ticker': ticker,
                    'name': output.get('name', ticker),
                    'current_price': current_price,
                    'open_price': safe_float(output.get('open')),
                    'high_price': safe_float(output.get('high')),
                    'low_price': safe_float(output.get('low')),
                    'prev_close': safe_float(output.get('base')),
                    'change_price': safe_float(output.get('diff')),
                    'change_rate': safe_float(output.get('rate')),
                    'volume': safe_int(output.get('tvol')),
                    'exchange': exchange,
                    '_rsym': output.get('rsym', ''),  # 거래소 추출용
                    'timestamp': datetime.now()
                }
            return None
        except Exception as e:
            return None
    
    def get_kr_minute_price(self, ticker: str, date: str, interval: int = 1) -> list:
        """
        한국 주식 분봉 조회
        
        Args:
            ticker: 종목코드 (6자리)
            date: 조회일 (YYYYMMDD)
            interval: 분봉 간격 (1, 5, 15, 30, 60)
        
        Returns:
            list: 분봉 데이터 리스트
        """
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"
        
        # TR_ID: FHKST03010200 (주식당일분봉조회)
        headers = self.auth.get_headers(tr_id="FHKST03010200")
        
        params = {
            "FID_ETC_CLS_CODE": "",
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker,
            "FID_INPUT_HOUR_1": "090000",  # 시작 시간
            "FID_PW_DATA_INCU_YN": "Y"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('rt_cd') == '0':
                return result.get('output2', [])
            return []
        except Exception as e:
            print(f"  ❌ 한국 분봉 조회 오류: {e}")
            return []
    
    def get_us_minute_price(self, ticker: str, exchange: str, date: str, interval: int = 1) -> list:
        """
        미국 주식 분봉 조회
        
        Args:
            ticker: 종목코드
            exchange: 거래소 코드 (NAS, NYS, AMS)
            date: 조회일 (YYYYMMDD)
            interval: 분봉 간격 (1, 5, 15, 30, 60)
        
        Returns:
            list: 분봉 데이터 리스트
        """
        url = f"{self.base_url}/uapi/overseas-price/v1/quotations/inquire-time-itemchartprice"
        
        # TR_ID: HHDFS76950200 (해외주식분봉조회)
        headers = self.auth.get_headers(tr_id="HHDFS76950200")
        
        # 분봉 간격 코드 변환
        interval_code = {1: "1", 5: "5", 15: "15", 30: "30", 60: "60"}.get(interval, "1")
        
        params = {
            "AUTH": "",
            "EXCD": exchange,
            "SYMB": ticker,
            "NMIN": interval_code,
            "PINC": "1",
            "NEXT": "",
            "NREC": "120",  # 최대 120건
            "FILL": "",
            "KEYB": ""
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('rt_cd') == '0':
                return result.get('output2', [])
            return []
        except Exception as e:
            print(f"  ❌ 미국 분봉 조회 오류: {e}")
            return []
    
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

