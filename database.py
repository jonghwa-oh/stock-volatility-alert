"""
SQLite 데이터베이스 관리 (Peewee ORM)
일봉 & 분봉 데이터 저장/조회
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from peewee import fn, IntegrityError

from models import (
    db, init_db, close_db,
    User, UserWatchlist, DailyPrice, MinutePrice,
    StatisticsCache, Setting, AlertHistory
)


class StockDatabase:
    """주식 데이터 관리 (Peewee ORM)"""
    
    def __init__(self, db_path: str = 'data/stock_data.db'):
        self.db_path = db_path
        init_db(db_path)
    
    def close(self):
        """DB 연결 종료"""
        close_db()
    
    # ========================================
    # 일봉 데이터
    # ========================================
    
    def insert_daily_price(self, ticker: str, ticker_name: str, date: str,
                          open_price: float, high: float, low: float,
                          close: float, volume: int) -> bool:
        """일봉 데이터 저장"""
        try:
            DailyPrice.insert(
                ticker=ticker,
                ticker_name=ticker_name,
                date=date,
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume
            ).on_conflict(
                conflict_target=[DailyPrice.ticker, DailyPrice.date],
                update={
                    DailyPrice.open: open_price,
                    DailyPrice.high: high,
                    DailyPrice.low: low,
                    DailyPrice.close: close,
                    DailyPrice.volume: volume
                }
            ).execute()
            return True
        except Exception as e:
            print(f"❌ 일봉 데이터 저장 실패 ({ticker}): {e}")
            return False
    
    def insert_daily_prices_bulk(self, data: List[tuple]) -> bool:
        """일봉 데이터 대량 저장"""
        try:
            with db.atomic():
                for row in data:
                    ticker, ticker_name, date, open_price, high, low, close, volume = row
                    DailyPrice.insert(
                        ticker=ticker,
                        ticker_name=ticker_name,
                        date=date,
                        open=open_price,
                        high=high,
                        low=low,
                        close=close,
                        volume=volume
                    ).on_conflict(
                        conflict_target=[DailyPrice.ticker, DailyPrice.date],
                        update={
                            DailyPrice.open: open_price,
                            DailyPrice.high: high,
                            DailyPrice.low: low,
                            DailyPrice.close: close,
                            DailyPrice.volume: volume
                        }
                    ).execute()
            return True
        except Exception as e:
            print(f"❌ 일봉 데이터 대량 저장 실패: {e}")
            return False
    
    def get_daily_prices(self, ticker: str, days: int = 252) -> pd.DataFrame:
        """일봉 데이터 조회 (최근 N일)"""
        query = (DailyPrice
                 .select(DailyPrice.date, DailyPrice.open, DailyPrice.high,
                        DailyPrice.low, DailyPrice.close, DailyPrice.volume)
                 .where(DailyPrice.ticker == ticker)
                 .order_by(DailyPrice.date.desc())
                 .limit(days))
        
        data = list(query.dicts())
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        df = df.sort_values('date').reset_index(drop=True)
        df['date'] = pd.to_datetime(df['date'])
        return df
    
    def get_daily_prices_range(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """일봉 데이터 조회 (날짜 범위)"""
        query = (DailyPrice
                 .select(DailyPrice.date, DailyPrice.open, DailyPrice.high,
                        DailyPrice.low, DailyPrice.close, DailyPrice.volume)
                 .where(
                     (DailyPrice.ticker == ticker) &
                     (DailyPrice.date >= start_date) &
                     (DailyPrice.date <= end_date)
                 )
                 .order_by(DailyPrice.date))
        
        data = list(query.dicts())
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        return df
    
    def get_latest_date(self, ticker: str) -> Optional[str]:
        """해당 종목의 최신 데이터 날짜"""
        result = (DailyPrice
                  .select(fn.MAX(DailyPrice.date))
                  .where(DailyPrice.ticker == ticker)
                  .scalar())
        return str(result) if result else None
    
    # ========================================
    # 분봉 데이터
    # ========================================
    
    def insert_minute_price(self, ticker: str, ticker_name: str,
                           datetime_str: str, price: float, volume: int = 0) -> bool:
        """분봉 데이터 저장"""
        try:
            MinutePrice.insert(
                ticker=ticker,
                ticker_name=ticker_name,
                datetime=datetime_str,
                price=price,
                volume=volume
            ).on_conflict(
                conflict_target=[MinutePrice.ticker, MinutePrice.datetime],
                update={MinutePrice.price: price, MinutePrice.volume: volume}
            ).execute()
            return True
        except Exception as e:
            print(f"❌ 분봉 데이터 저장 실패 ({ticker}): {e}")
            return False
    
    def insert_minute_prices_bulk(self, data: List[tuple]) -> bool:
        """분봉 데이터 대량 저장"""
        try:
            with db.atomic():
                for row in data:
                    ticker, ticker_name, datetime_str, price, volume = row
                    MinutePrice.insert(
                        ticker=ticker,
                        ticker_name=ticker_name,
                        datetime=datetime_str,
                        price=price,
                        volume=volume
                    ).on_conflict(
                        conflict_target=[MinutePrice.ticker, MinutePrice.datetime],
                        update={MinutePrice.price: price, MinutePrice.volume: volume}
                    ).execute()
            return True
        except Exception as e:
            print(f"❌ 분봉 데이터 대량 저장 실패: {e}")
            return False
    
    def get_minute_prices(self, ticker: str, hours: int = 24) -> pd.DataFrame:
        """분봉 데이터 조회 (최근 N시간)"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        query = (MinutePrice
                 .select(MinutePrice.datetime, MinutePrice.price, MinutePrice.volume)
                 .where(
                     (MinutePrice.ticker == ticker) &
                     (MinutePrice.datetime >= cutoff_time)
                 )
                 .order_by(MinutePrice.datetime))
        
        data = list(query.dicts())
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        return df
    
    # ========================================
    # 통계 캐시
    # ========================================
    
    def update_statistics_cache(self, ticker: str, date: str,
                                mean_return: float, std_dev: float,
                                current_price: float, target_1sigma: float,
                                target_2sigma: float) -> bool:
        """통계 캐시 업데이트"""
        try:
            StatisticsCache.insert(
                ticker=ticker,
                date=date,
                mean_return=mean_return,
                std_dev=std_dev,
                current_price=current_price,
                target_1sigma=target_1sigma,
                target_2sigma=target_2sigma
            ).on_conflict(
                conflict_target=[StatisticsCache.ticker, StatisticsCache.date],
                update={
                    StatisticsCache.mean_return: mean_return,
                    StatisticsCache.std_dev: std_dev,
                    StatisticsCache.current_price: current_price,
                    StatisticsCache.target_1sigma: target_1sigma,
                    StatisticsCache.target_2sigma: target_2sigma,
                    StatisticsCache.updated_at: datetime.now()
                }
            ).execute()
            return True
        except Exception as e:
            print(f"❌ 통계 캐시 업데이트 실패 ({ticker}): {e}")
            return False
    
    def get_statistics_cache(self, ticker: str, date: str = None) -> Optional[Dict]:
        """통계 캐시 조회"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            cache = StatisticsCache.get(
                (StatisticsCache.ticker == ticker) &
                (StatisticsCache.date == date)
            )
            return {
                'mean_return': cache.mean_return,
                'std_dev': cache.std_dev,
                'current_price': cache.current_price,
                'target_1sigma': cache.target_1sigma,
                'target_2sigma': cache.target_2sigma,
                'updated_at': str(cache.updated_at)
            }
        except StatisticsCache.DoesNotExist:
            return None
    
    # ========================================
    # 유틸리티
    # ========================================
    
    def get_all_tickers(self) -> List[str]:
        """저장된 모든 종목 코드"""
        query = DailyPrice.select(DailyPrice.ticker).distinct()
        return [row.ticker for row in query]
    
    def get_data_status(self) -> Dict:
        """데이터 현황"""
        daily_count = DailyPrice.select().count()
        daily_tickers = DailyPrice.select(DailyPrice.ticker).distinct().count()
        daily_min = DailyPrice.select(fn.MIN(DailyPrice.date)).scalar()
        daily_max = DailyPrice.select(fn.MAX(DailyPrice.date)).scalar()
        
        minute_count = MinutePrice.select().count()
        minute_tickers = MinutePrice.select(MinutePrice.ticker).distinct().count()
        minute_min = MinutePrice.select(fn.MIN(MinutePrice.datetime)).scalar()
        minute_max = MinutePrice.select(fn.MAX(MinutePrice.datetime)).scalar()
        
        return {
            'daily': {
                'total_rows': daily_count,
                'tickers': daily_tickers,
                'date_range': (str(daily_min) if daily_min else None,
                              str(daily_max) if daily_max else None)
            },
            'minute': {
                'total_rows': minute_count,
                'tickers': minute_tickers,
                'datetime_range': (str(minute_min) if minute_min else None,
                                  str(minute_max) if minute_max else None)
            }
        }
    
    def cleanup_old_minute_data(self, days: int = 30) -> int:
        """오래된 분봉 데이터 삭제"""
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted = MinutePrice.delete().where(MinutePrice.datetime < cutoff_date).execute()
        print(f"✅ {deleted}개 오래된 분봉 데이터 삭제 ({days}일 이전)")
        return deleted
    
    def backup_database(self, backup_path: str) -> bool:
        """데이터베이스 백업"""
        import shutil
        try:
            shutil.copy2(self.db_path, backup_path)
            print(f"✅ 백업 완료: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ 백업 실패: {e}")
            return False
    
    # ========================================
    # 사용자 관리
    # ========================================
    
    def add_user(self, name: str, ntfy_topic: str = None) -> Optional[int]:
        """사용자 추가"""
        try:
            user = User.create(name=name, ntfy_topic=ntfy_topic)
            print(f"✅ 사용자 추가: {name}")
            return user.id
        except IntegrityError:
            print(f"⚠️  이미 존재하는 사용자: {name}")
            return None
        except Exception as e:
            print(f"❌ 사용자 추가 실패: {e}")
            return None
    
    def get_user(self, name: str) -> Optional[Dict]:
        """사용자 정보 조회"""
        try:
            user = User.get(User.name == name)
            return {
                'id': user.id,
                'name': user.name,
                'enabled': user.enabled,
                'ntfy_topic': user.ntfy_topic
            }
        except User.DoesNotExist:
            return None
    
    def get_all_users(self, include_disabled: bool = False) -> List[Dict]:
        """모든 사용자 조회"""
        query = User.select()
        if not include_disabled:
            query = query.where(User.enabled == True)
        
        return [{
            'id': user.id,
            'name': user.name,
            'enabled': user.enabled,
            'notification_enabled': user.notification_enabled,
            'password_hash': user.password_hash,
            'ntfy_topic': user.ntfy_topic
        } for user in query]
    
    def set_user_password(self, name: str, password_hash: str) -> bool:
        """사용자 비밀번호 설정"""
        try:
            updated = User.update(password_hash=password_hash).where(User.name == name).execute()
            return updated > 0
        except Exception as e:
            print(f"❌ 비밀번호 설정 실패: {e}")
            return False
    
    def get_user_by_name(self, name: str) -> Optional[Dict]:
        """사용자 정보 조회 (웹 로그인용, 비밀번호 해시 포함)"""
        try:
            user = User.get(User.name == name)
            return {
                'id': user.id,
                'name': user.name,
                'enabled': user.enabled,
                'notification_enabled': user.notification_enabled,
                'password_hash': user.password_hash,
                'ntfy_topic': user.ntfy_topic
            }
        except User.DoesNotExist:
            return None
    
    def set_user_ntfy_topic(self, name: str, ntfy_topic: str) -> bool:
        """사용자 ntfy 토픽 설정"""
        try:
            updated = User.update(ntfy_topic=ntfy_topic).where(User.name == name).execute()
            return updated > 0
        except Exception as e:
            print(f"❌ ntfy 토픽 설정 실패: {e}")
            return False
    
    def get_user_ntfy_topic(self, user_id: int) -> Optional[str]:
        """사용자 ntfy 토픽 조회"""
        try:
            user = User.get_by_id(user_id)
            return user.ntfy_topic
        except User.DoesNotExist:
            return None
    
    def verify_user_password(self, name: str, password_hash: str) -> bool:
        """비밀번호 검증"""
        try:
            user = User.get(User.name == name)
            return user.password_hash == password_hash
        except User.DoesNotExist:
            return False
    
    def update_user_notification(self, name: str, enabled: bool) -> bool:
        """알림 설정 업데이트"""
        try:
            updated = User.update(notification_enabled=enabled).where(User.name == name).execute()
            return updated > 0
        except Exception as e:
            print(f"❌ 알림 설정 업데이트 실패: {e}")
            return False
    
    # ========================================
    # 관심 종목 관리
    # ========================================
    
    def add_user_watchlist(self, user_name: str, ticker: str, name: str = None,
                          country: str = 'US', investment_amount: float = None) -> bool:
        """사용자 관심 종목 추가"""
        user = self.get_user(user_name)
        if not user:
            print(f"❌ 사용자 없음: {user_name}")
            return False
        
        stock_name = name or ticker
        
        try:
            UserWatchlist.insert(
                user=user['id'],
                ticker=ticker,
                name=stock_name,
                country=country,
                investment_amount=investment_amount
            ).on_conflict(
                conflict_target=[UserWatchlist.user, UserWatchlist.ticker],
                update={
                    UserWatchlist.enabled: True,
                    UserWatchlist.name: stock_name,
                    UserWatchlist.country: country,
                    UserWatchlist.investment_amount: investment_amount
                }
            ).execute()
            print(f"✅ 관심 종목 추가: {stock_name}({ticker}) [{country}]")
            return True
        except Exception as e:
            print(f"❌ 관심 종목 추가 실패: {e}")
            return False
    
    def remove_user_watchlist(self, user_name: str, ticker: str) -> bool:
        """사용자 관심 종목 제거 (비활성화)"""
        user = self.get_user(user_name)
        if not user:
            return False
        
        try:
            updated = (UserWatchlist
                      .update(enabled=False)
                      .where(
                          (UserWatchlist.user == user['id']) &
                          (UserWatchlist.ticker == ticker)
                      ).execute())
            return updated > 0
        except Exception as e:
            print(f"❌ 관심 종목 제거 실패: {e}")
            return False
    
    def update_watchlist_investment(self, user_name: str, ticker: str,
                                   investment_amount: float) -> bool:
        """종목별 투자금액 업데이트"""
        user = self.get_user(user_name)
        if not user:
            return False
        
        try:
            updated = (UserWatchlist
                      .update(investment_amount=investment_amount)
                      .where(
                          (UserWatchlist.user == user['id']) &
                          (UserWatchlist.ticker == ticker)
                      ).execute())
            return updated > 0
        except Exception as e:
            print(f"❌ 투자금액 업데이트 실패: {e}")
            return False
    
    def get_user_watchlist(self, user_name: str) -> List[str]:
        """사용자 관심 종목 목록 (티커만)"""
        user = self.get_user(user_name)
        if not user:
            return []
        
        query = (UserWatchlist
                 .select(UserWatchlist.ticker)
                 .where(
                     (UserWatchlist.user == user['id']) &
                     (UserWatchlist.enabled == True)
                 ))
        return [w.ticker for w in query]
    
    def get_user_watchlist_with_names(self, user_name: str) -> List[Dict]:
        """사용자 관심 종목 목록 (종목명 + 국가 + 투자금액 포함)"""
        user = self.get_user(user_name)
        if not user:
            return []
        
        query = (UserWatchlist
                 .select()
                 .where(
                     (UserWatchlist.user == user['id']) &
                     (UserWatchlist.enabled == True)
                 ))
        
        watchlist = []
        for w in query:
            # daily_prices에서 이름 가져오기 (없으면 watchlist 이름 사용)
            dp = (DailyPrice
                  .select(DailyPrice.ticker_name)
                  .where(DailyPrice.ticker == w.ticker)
                  .order_by(DailyPrice.date.desc())
                  .first())
            
            name = w.name or (dp.ticker_name if dp else w.ticker)
            
            watchlist.append({
                'ticker': w.ticker,
                'name': name,
                'country': w.country or 'US',
                'investment_amount': w.investment_amount
            })
        return watchlist
    
    def get_user_watchlist_with_country(self, user_name: str) -> List[Dict]:
        """사용자 관심 종목 목록 (종목명 + 국가 정보 포함)"""
        return self.get_user_watchlist_with_names(user_name)
    
    # ========================================
    # 설정 관리
    # ========================================
    
    def save_setting(self, key: str, value: str, description: str = None):
        """설정 저장"""
        Setting.insert(
            key=key,
            value=value,
            description=description
        ).on_conflict(
            conflict_target=[Setting.key],
            update={
                Setting.value: value,
                Setting.description: description,
                Setting.updated_at: datetime.now()
            }
        ).execute()
        print(f"✅ 설정 저장: {key}")
    
    def get_setting(self, key: str, default=None) -> Optional[str]:
        """설정 조회"""
        try:
            setting = Setting.get(Setting.key == key)
            return setting.value
        except Setting.DoesNotExist:
            return default
    
    def list_settings(self) -> List[Dict]:
        """모든 설정 조회"""
        return [{
            'key': s.key,
            'value': s.value,
            'description': s.description
        } for s in Setting.select().order_by(Setting.key)]
    
    def delete_setting(self, key: str):
        """설정 삭제"""
        Setting.delete().where(Setting.key == key).execute()
        print(f"✅ 설정 삭제: {key}")
    
    # ========================================
    # 알림 이력
    # ========================================
    
    def add_alert_history(self, user_id: int, ticker: str, ticker_name: str,
                         country: str, alert_level: str, target_price: float,
                         current_price: float, drop_rate: float, sent: bool = False) -> bool:
        """알림 이력 추가"""
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        
        try:
            AlertHistory.insert(
                user=user_id,
                ticker=ticker,
                ticker_name=ticker_name,
                country=country,
                alert_level=alert_level,
                alert_date=today,
                target_price=target_price,
                current_price=current_price,
                drop_rate=drop_rate,
                alert_time=now,
                sent=sent
            ).on_conflict_ignore().execute()
            return True
        except IntegrityError:
            return False
    
    def get_user_alerts(self, user_id: int, ticker: str = None, limit: int = 50) -> List[Dict]:
        """사용자 알림 내역 조회"""
        query = AlertHistory.select()
        
        if ticker:
            query = query.where(
                (AlertHistory.user == user_id) &
                (AlertHistory.ticker == ticker)
            )
        else:
            query = query.where(AlertHistory.user == user_id)
        
        query = query.order_by(AlertHistory.alert_time.desc()).limit(limit)
        
        alerts = []
        for alert in query:
            # 투자금액 가져오기
            watchlist = (UserWatchlist
                        .select(UserWatchlist.investment_amount)
                        .where(
                            (UserWatchlist.user == user_id) &
                            (UserWatchlist.ticker == alert.ticker)
                        ).first())
            
            investment_amount = watchlist.investment_amount if watchlist else None
            
            # 매수 수량 계산
            shares = 0
            if investment_amount and investment_amount > 0 and alert.current_price > 0:
                shares = int(investment_amount / alert.current_price)
            
            alerts.append({
                'id': alert.id,
                'ticker': alert.ticker,
                'ticker_name': alert.ticker_name,
                'country': alert.country,
                'alert_level': alert.alert_level,
                'alert_date': alert.alert_date,
                'target_price': alert.target_price,
                'current_price': alert.current_price,
                'drop_rate': alert.drop_rate,
                'alert_time': str(alert.alert_time),
                'sent': alert.sent,
                'investment_amount': investment_amount,
                'shares': shares
            })
        return alerts
    
    def check_alert_exists(self, user_id: int, ticker: str, alert_date: str,
                          alert_level: str) -> bool:
        """알림 중복 체크"""
        return AlertHistory.select().where(
            (AlertHistory.user == user_id) &
            (AlertHistory.ticker == ticker) &
            (AlertHistory.alert_date == alert_date) &
            (AlertHistory.alert_level == alert_level)
        ).exists()
    
    def get_alerts_by_ticker(self, user_id: int, limit: int = 100) -> Dict[str, List[Dict]]:
        """종목별 알림 내역 조회 (그룹화)"""
        alerts = self.get_user_alerts(user_id, limit=limit)
        
        # 종목별로 그룹화
        by_ticker = {}
        for alert in alerts:
            ticker = alert['ticker']
            if ticker not in by_ticker:
                by_ticker[ticker] = []
            by_ticker[ticker].append(alert)
        
        return by_ticker


# 테스트
if __name__ == "__main__":
    db = StockDatabase()
    
    print("\n📊 데이터베이스 현황:")
    status = db.get_data_status()
    print(f"일봉 데이터: {status['daily']['total_rows']:,}개 ({status['daily']['tickers']}개 종목)")
    print(f"분봉 데이터: {status['minute']['total_rows']:,}개 ({status['minute']['tickers']}개 종목)")
    
    if status['daily']['date_range'][0]:
        print(f"일봉 기간: {status['daily']['date_range'][0]} ~ {status['daily']['date_range'][1]}")
    
    if status['minute']['datetime_range'][0]:
        print(f"분봉 기간: {status['minute']['datetime_range'][0]} ~ {status['minute']['datetime_range'][1]}")
    
    db.close()
