"""
한국투자증권 API 초기 설정 스크립트
"""
from kis_crypto import KISCrypto


def init_kis_settings():
    """한국투자증권 API 설정 초기화"""
    print("\n" + "="*70)
    print("🏦 한국투자증권 Open Trading API 설정")
    print("="*70)
    
    print("\n📝 API 인증 정보를 입력해주세요:")
    print("   (한국투자증권 홈페이지 또는 앱에서 발급받은 정보)")
    
    app_key = input("\n  App Key: ").strip()
    app_secret = input("  App Secret: ").strip()
    
    print("\n📝 계좌 정보를 입력해주세요:")
    print("   (선택 사항, 나중에 추가 가능)")
    
    account_no = input("\n  계좌번호 앞 8자리 (선택): ").strip() or None
    
    if account_no:
        print("\n  계좌번호 뒤 2자리 선택:")
        print("    01: 종합계좌 (기본)")
        print("    03: 국내선물옵션")
        print("    08: 해외선물옵션")
        print("    22: 연금저축")
        print("    29: 퇴직연금")
        account_code = input("\n  선택 (기본 01): ").strip() or "01"
    else:
        account_code = "01"
    
    # 저장
    crypto = KISCrypto()
    crypto.save_kis_credentials(
        app_key=app_key,
        app_secret=app_secret,
        account_no=account_no,
        account_code=account_code
    )
    
    print("\n" + "="*70)
    print("✅ 한국투자증권 API 설정 완료!")
    print("="*70)
    print(f"\n💾 저장된 정보:")
    print(f"  • App Key: {app_key[:10]}..." + "*" * (len(app_key) - 10))
    print(f"  • App Secret: {app_secret[:10]}..." + "*" * (len(app_secret) - 10))
    if account_no:
        print(f"  • 계좌번호: {account_no[:4]}****-{account_code}")
    print(f"\n🔐 모든 정보는 암호화되어 저장되었습니다.")
    print(f"📁 암호화 키 위치: data/.kis_key")
    print(f"📁 설정 DB 위치: data/stock_data.db")
    
    print("\n" + "="*70)
    print("🧪 인증 정보 테스트")
    print("="*70)
    
    # 로드 테스트
    try:
        credentials = crypto.load_kis_credentials()
        print("✅ 저장된 정보 로드 성공!")
        print(f"  • App Key 복호화: {credentials['app_key'][:10]}...")
        print(f"  • App Secret 복호화: {credentials['app_secret'][:10]}...")
        if credentials['account_no']:
            print(f"  • 계좌번호 복호화: {credentials['account_no'][:4]}****-{credentials['account_code']}")
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    print("\n" + "="*70)
    print("📚 다음 단계:")
    print("="*70)
    print("1. python kis_auth.py           # 토큰 발급 테스트")
    print("2. python test_kis_api.py       # API 연결 테스트")
    print("3. python data_collector.py     # 데이터 수집 테스트")
    print("="*70)


if __name__ == "__main__":
    init_kis_settings()



