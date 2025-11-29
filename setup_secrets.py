"""
초기 설정 스크립트
민감한 정보를 암호화하여 DB에 저장
"""

import os
from pathlib import Path
from secrets_manager import SecretsManager, generate_master_key


def create_env_file():
    """
    .env 파일 생성 (마스터 키)
    """
    env_file = Path('.env')
    
    if env_file.exists():
        print("✅ .env 파일이 이미 존재합니다.")
        with open(env_file, 'r') as f:
            content = f.read()
            if 'MASTER_KEY=' in content:
                return True
            print("⚠️  MASTER_KEY가 없습니다. 추가합니다...")
    
    # 새로운 마스터 키 생성
    master_key = generate_master_key()
    
    print("\n🔑 새로운 마스터 키 생성")
    print("="*60)
    print(f"MASTER_KEY={master_key}")
    print("="*60)
    
    # .env 파일에 저장
    with open(env_file, 'a') as f:
        f.write(f"\nMASTER_KEY={master_key}\n")
    
    print(f"\n✅ .env 파일에 저장되었습니다.")
    print("⚠️  이 파일은 절대 Git에 올리지 마세요!")
    
    return True


def setup_telegram_config():
    """텔레그램 설정"""
    print("\n📱 텔레그램 봇 설정")
    print("="*60)
    
    bot_token = input("텔레그램 Bot Token: ").strip()
    if not bot_token:
        print("❌ Bot Token은 필수입니다.")
        return False
    
    chat_id = input("텔레그램 Chat ID: ").strip()
    if not chat_id:
        print("❌ Chat ID는 필수입니다.")
        return False
    
    return bot_token, chat_id


def setup_investment_config():
    """투자 설정"""
    print("\n💰 투자 설정")
    print("="*60)
    
    amount = input("기본 투자 금액 (원) [기본값: 1000000]: ").strip()
    if not amount:
        amount = "1000000"
    
    try:
        int(amount)
        return amount
    except ValueError:
        print("⚠️  잘못된 금액입니다. 기본값 1000000 사용")
        return "1000000"


def main():
    """메인 설정 프로세스"""
    print("\n" + "="*60)
    print("🔐 주식 알림 시스템 초기 설정")
    print("="*60)
    
    # 1. .env 파일 생성
    print("\n[1/3] 마스터 키 생성")
    if not create_env_file():
        return
    
    # 2. SecretsManager 초기화
    try:
        # 환경변수 다시 로드
        os.environ.clear()
        env_file = Path('.env')
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        sm = SecretsManager()
        print("\n✅ Secrets Manager 초기화 성공")
    except Exception as e:
        print(f"\n❌ Secrets Manager 초기화 실패: {e}")
        return
    
    # 3. 텔레그램 설정
    print("\n[2/3] 텔레그램 봇 설정")
    telegram_config = setup_telegram_config()
    if not telegram_config:
        return
    
    bot_token, chat_id = telegram_config
    sm.set_secret('BOT_TOKEN', bot_token)
    sm.set_secret('CHAT_ID', chat_id)
    
    # 4. 투자 설정
    print("\n[3/3] 투자 금액 설정")
    amount = setup_investment_config()
    sm.set_secret('DEFAULT_AMOUNT', amount)
    
    # 5. 완료
    print("\n" + "="*60)
    print("✅ 설정 완료!")
    print("="*60)
    print("\n📁 생성된 파일:")
    print("  • .env (마스터 키)")
    print("  • secrets.db (암호화된 설정)")
    print("\n⚠️  중요:")
    print("  • 이 파일들은 .gitignore에 포함되어 있습니다.")
    print("  • GitHub에 절대 올리지 마세요!")
    print("  • 백업은 안전한 곳에 별도로 보관하세요.")
    
    print("\n📊 저장된 설정:")
    keys = sm.list_keys()
    for key, created, updated in keys:
        print(f"  • {key}")
    
    print("\n🚀 다음 단계:")
    print("  1. python data_collector.py init  # DB 초기화")
    print("  2. python user_manager.py family  # 사용자 설정")
    print("  3. python realtime_monitor_multiuser.py  # 실행")
    print("\n또는 Docker:")
    print("  docker-compose up -d")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 설정이 취소되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

