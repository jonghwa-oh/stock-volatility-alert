"""
초기 설정 스크립트
텔레그램 봇 토큰 및 기본 설정 입력
"""

from database import StockDatabase


def init_settings():
    """초기 설정"""
    db = StockDatabase()
    
    print("\n" + "="*60)
    print("🔧 초기 설정")
    print("="*60)
    
    # 텔레그램 봇 토큰
    print("\n📱 텔레그램 봇 설정")
    bot_token = input("Bot Token: ").strip()
    if bot_token:
        db.save_setting('bot_token', bot_token, '텔레그램 봇 토큰')
    
    # 기본 Chat ID (선택)
    default_chat_id = input("기본 Chat ID (선택, Enter 스킵): ").strip()
    if default_chat_id:
        db.save_setting('default_chat_id', default_chat_id, '기본 Chat ID')
    
    # 기본 투자 금액
    print("\n💰 기본 투자 금액")
    default_amount = input("기본 투자 금액 (원) [1000000]: ").strip() or "1000000"
    db.save_setting('default_investment_amount', default_amount, '기본 투자 금액')
    
    print("\n" + "="*60)
    print("✅ 초기 설정 완료!")
    print("="*60)
    
    # 설정 확인
    print("\n📋 저장된 설정:")
    settings = db.list_settings()
    for s in settings:
        value = s['value']
        # 토큰은 앞뒤만 표시
        if 'token' in s['key'].lower() and len(value) > 20:
            value = value[:10] + '...' + value[-10:]
        print(f"  • {s['key']}: {value}")
        if s['description']:
            print(f"    ({s['description']})")
    
    db.close()


if __name__ == "__main__":
    try:
        init_settings()
    except KeyboardInterrupt:
        print("\n\n❌ 취소되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


