"""
Peewee ORM 모델 정의
"""

from peewee import *
import datetime as dt

# 데이터베이스 연결
db = SqliteDatabase(None)  # 나중에 init()에서 경로 설정


class BaseModel(Model):
    """기본 모델"""
    class Meta:
        database = db


class User(BaseModel):
    """사용자"""
    id = AutoField()
    name = CharField(unique=True)
    password_hash = CharField(null=True)
    ntfy_topic = CharField(null=True)
    enabled = BooleanField(default=True)
    notification_enabled = BooleanField(default=True)
    created_at = DateTimeField(default=dt.datetime.now)

    class Meta:
        table_name = 'users'


class UserWatchlist(BaseModel):
    """사용자별 관심 종목"""
    id = AutoField()
    user = ForeignKeyField(User, column_name='user_id', backref='watchlist', on_delete='CASCADE')
    ticker = CharField()
    name = CharField(null=True)
    country = CharField(default='US')
    investment_amount = FloatField(null=True)
    enabled = BooleanField(default=True)
    added_at = DateTimeField(default=dt.datetime.now)

    class Meta:
        table_name = 'user_watchlist'
        indexes = (
            (('user', 'ticker'), True),  # UNIQUE
        )


class DailyPrice(BaseModel):
    """일봉 데이터"""
    id = AutoField()
    ticker = CharField()
    ticker_name = CharField()
    date = DateField()
    open = FloatField(null=True)
    high = FloatField(null=True)
    low = FloatField(null=True)
    close = FloatField()
    volume = IntegerField(null=True)
    created_at = DateTimeField(default=dt.datetime.now)

    class Meta:
        table_name = 'daily_prices'
        indexes = (
            (('ticker', 'date'), True),  # UNIQUE
        )


class MinutePrice(BaseModel):
    """분봉 데이터"""
    id = AutoField()
    ticker = CharField()
    ticker_name = CharField()
    datetime = DateTimeField()
    datetime_utc = DateTimeField(null=True)
    market_date = DateField(null=True)
    price = FloatField()
    volume = IntegerField(null=True)
    created_at = DateTimeField(default=dt.datetime.now)

    class Meta:
        table_name = 'minute_prices'
        indexes = (
            (('ticker', 'datetime'), True),  # UNIQUE
        )


class StatisticsCache(BaseModel):
    """통계 캐시"""
    id = AutoField()
    ticker = CharField()
    ticker_name = CharField(null=True)
    country = CharField(default='US')
    date = DateField()
    data_date = DateField(null=True)
    mean_return = FloatField(null=True)
    std_dev = FloatField(null=True)
    current_price = FloatField(null=True)
    target_05sigma = FloatField(null=True)
    target_1sigma = FloatField(null=True)
    target_2sigma = FloatField(null=True)
    drop_05x = FloatField(null=True)
    drop_1x = FloatField(null=True)
    drop_2x = FloatField(null=True)
    updated_at = DateTimeField(default=dt.datetime.now)

    class Meta:
        table_name = 'statistics_cache'
        indexes = (
            (('ticker', 'date'), True),  # UNIQUE
        )


class Setting(BaseModel):
    """설정"""
    key = CharField(primary_key=True)
    value = TextField()
    description = TextField(null=True)
    created_at = DateTimeField(default=dt.datetime.now)
    updated_at = DateTimeField(default=dt.datetime.now)

    class Meta:
        table_name = 'settings'


class AlertHistory(BaseModel):
    """알림 이력"""
    id = AutoField()
    user = ForeignKeyField(User, column_name='user_id', backref='alerts', null=True, on_delete='SET NULL')
    ticker = CharField()
    ticker_name = CharField()
    country = CharField()
    alert_level = CharField()
    alert_date = CharField()
    target_price = FloatField()
    current_price = FloatField()
    drop_rate = FloatField()
    alert_time = DateTimeField()
    sent = BooleanField(default=False)
    created_at = DateTimeField(default=dt.datetime.now)

    class Meta:
        table_name = 'alert_history'
        indexes = (
            (('user', 'ticker', 'alert_date', 'alert_level'), True),  # UNIQUE
        )


# 모든 모델 리스트
ALL_MODELS = [
    User,
    UserWatchlist,
    DailyPrice,
    MinutePrice,
    StatisticsCache,
    Setting,
    AlertHistory,
]


def init_db(db_path: str = 'data/stock_data.db'):
    """데이터베이스 초기화"""
    db.init(db_path)
    db.connect(reuse_if_open=True)
    # 테이블이 없으면 생성 (기존 데이터 유지)
    db.create_tables(ALL_MODELS, safe=True)
    print(f"✅ Peewee DB 초기화 완료: {db_path}")
    return db


def close_db():
    """데이터베이스 연결 종료"""
    if not db.is_closed():
        db.close()

