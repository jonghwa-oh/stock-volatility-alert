"""
사용자 관리 도구
가족 구성원별 설정
"""

from database import StockDatabase
from scheduler_config import WATCH_LIST


class UserManager:
    """사용자 관리"""
    
    def __init__(self):
        self.db = StockDatabase()
    
    def add_user(self, name: str, chat_id: str, investment_amount: float = 1000000):
        """새 사용자 추가"""
        user_id = self.db.add_user(name, chat_id, investment_amount)
        if user_id:
            print(f"\n✅ 사용자 추가 완료!")
            print(f"   • 이름: {name}")
            print(f"   • Chat ID: {chat_id}")
            print(f"   • 투자 금액: {investment_amount:,.0f}원")
            return True
        return False
    
    def list_users(self):
        """사용자 목록"""
        users = self.db.get_all_users()
        
        if not users:
            print("\n⚠️  등록된 사용자가 없습니다.")
            return
        
        print("\n" + "="*60)
        print("👥 등록된 사용자")
        print("="*60)
        
        for user in users:
            print(f"\n📱 {user['name']}")
            print(f"   • Chat ID: {user['chat_id']}")
            print(f"   • 투자 금액: {user['investment_amount']:,.0f}원")
            
            # 관심 종목
            watchlist = self.db.get_user_watchlist_with_names(user['name'])
            if watchlist:
                print(f"   • 관심 종목 ({len(watchlist)}개):")
                for item in watchlist:
                    print(f"     - {item['ticker']}: {item['name']}")
            else:
                print(f"   • 관심 종목: 없음")
    
    def add_watchlist(self, user_name: str, tickers: list):
        """사용자에게 관심 종목 추가"""
        user = self.db.get_user(user_name)
        if not user:
            print(f"❌ 사용자 없음: {user_name}")
            return False
        
        success_count = 0
        for ticker in tickers:
            if self.db.add_user_watchlist(user_name, ticker):
                success_count += 1
        
        print(f"\n✅ {user_name}에게 {success_count}개 종목 추가")
        return True
    
    def remove_watchlist(self, user_name: str, tickers: list):
        """사용자 관심 종목 제거"""
        success_count = 0
        for ticker in tickers:
            if self.db.remove_user_watchlist(user_name, ticker):
                success_count += 1
        
        print(f"\n✅ {user_name}에게서 {success_count}개 종목 제거")
        return True
    
    def show_user_detail(self, user_name: str):
        """사용자 상세 정보"""
        user = self.db.get_user(user_name)
        if not user:
            print(f"❌ 사용자 없음: {user_name}")
            return
        
        print("\n" + "="*60)
        print(f"📱 {user['name']} 상세 정보")
        print("="*60)
        print(f"Chat ID: {user['chat_id']}")
        print(f"투자 금액: {user['investment_amount']:,.0f}원")
        print(f"상태: {'활성화' if user['enabled'] else '비활성화'}")
        
        watchlist = self.db.get_user_watchlist_with_names(user_name)
        print(f"\n📊 관심 종목 ({len(watchlist)}개):")
        
        if watchlist:
            for item in watchlist:
                print(f"  • {item['ticker']}: {item['name']}")
        else:
            print("  (없음)")
    
    def close(self):
        """DB 연결 종료"""
        self.db.close()


def interactive_setup():
    """대화형 사용자 설정"""
    manager = UserManager()
    
    print("\n" + "="*60)
    print("👨‍👩‍👦 가족용 멀티 유저 설정")
    print("="*60)
    
    while True:
        print("\n메뉴:")
        print("  1. 사용자 추가")
        print("  2. 관심 종목 추가")
        print("  3. 관심 종목 제거")
        print("  4. 사용자 목록")
        print("  5. 사용자 상세")
        print("  6. 종료")
        
        choice = input("\n선택 (1-6): ").strip()
        
        if choice == '1':
            # 사용자 추가
            print("\n" + "="*60)
            print("새 사용자 추가")
            print("="*60)
            
            name = input("이름 (예: 아빠, 엄마, 아들): ").strip()
            if not name:
                print("❌ 이름을 입력하세요")
                continue
            
            chat_id = input("텔레그램 Chat ID: ").strip()
            if not chat_id:
                print("❌ Chat ID를 입력하세요")
                continue
            
            amount_input = input("투자 금액 (기본 1,000,000원): ").strip()
            amount = float(amount_input) if amount_input else 1000000
            
            manager.add_user(name, chat_id, amount)
        
        elif choice == '2':
            # 관심 종목 추가
            print("\n사용 가능한 종목:")
            for idx, (ticker, ticker_name) in enumerate(WATCH_LIST.items(), 1):
                print(f"  {idx}. {ticker}: {ticker_name}")
            
            name = input("\n사용자 이름: ").strip()
            tickers_input = input("종목 코드 (쉼표로 구분, 예: TQQQ,SOXL,QLD): ").strip()
            
            if name and tickers_input:
                tickers = [t.strip().upper() for t in tickers_input.split(',')]
                manager.add_watchlist(name, tickers)
        
        elif choice == '3':
            # 관심 종목 제거
            name = input("사용자 이름: ").strip()
            tickers_input = input("제거할 종목 코드 (쉼표로 구분): ").strip()
            
            if name and tickers_input:
                tickers = [t.strip().upper() for t in tickers_input.split(',')]
                manager.remove_watchlist(name, tickers)
        
        elif choice == '4':
            # 사용자 목록
            manager.list_users()
        
        elif choice == '5':
            # 사용자 상세
            name = input("사용자 이름: ").strip()
            if name:
                manager.show_user_detail(name)
        
        elif choice == '6':
            # 종료
            print("\n✅ 종료합니다.")
            break
        
        else:
            print("❌ 잘못된 선택입니다.")
    
    manager.close()


def quick_setup_family():
    """빠른 가족 설정 (예시)"""
    manager = UserManager()
    
    print("\n" + "="*60)
    print("👨‍👩‍👦 가족용 빠른 설정")
    print("="*60)
    print("\n3명의 사용자를 설정합니다.")
    print("각자의 텔레그램 Chat ID가 필요합니다.\n")
    
    # 아빠
    print("1️⃣ 첫 번째 사용자 (본인)")
    dad_chat_id = input("  텔레그램 Chat ID: ").strip()
    if dad_chat_id:
        manager.add_user("아빠", dad_chat_id, 1000000)
        
        print("\n관심 종목 추가:")
        print("  추천: 레버리지 ETF (TQQQ, SOXL, QLD)")
        tickers = input("  종목 코드 (쉼표로 구분, 엔터=추천): ").strip()
        if not tickers:
            tickers = "TQQQ,SOXL,QLD"
        manager.add_watchlist("아빠", [t.strip().upper() for t in tickers.split(',')])
    
    # 엄마
    print("\n2️⃣ 두 번째 사용자 (배우자)")
    mom_chat_id = input("  텔레그램 Chat ID: ").strip()
    if mom_chat_id:
        manager.add_user("엄마", mom_chat_id, 1000000)
        
        print("\n관심 종목 추가:")
        print("  추천: 안정적인 ETF (SPY, QQQ, VOO)")
        tickers = input("  종목 코드 (쉼표로 구분, 엔터=추천): ").strip()
        if not tickers:
            tickers = "SPY,QQQ,VOO"
        manager.add_watchlist("엄마", [t.strip().upper() for t in tickers.split(',')])
    
    # 아들
    print("\n3️⃣ 세 번째 사용자 (자녀)")
    son_chat_id = input("  텔레그램 Chat ID: ").strip()
    if son_chat_id:
        manager.add_user("아들", son_chat_id, 500000)
        
        print("\n관심 종목 추가:")
        print("  추천: 기술주 ETF (XLK, TECL)")
        tickers = input("  종목 코드 (쉼표로 구분, 엔터=추천): ").strip()
        if not tickers:
            tickers = "XLK,TECL,QQQ"
        manager.add_watchlist("아들", [t.strip().upper() for t in tickers.split(',')])
    
    print("\n" + "="*60)
    print("✅ 가족 설정 완료!")
    print("="*60)
    
    manager.list_users()
    manager.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'setup':
            # 대화형 설정
            interactive_setup()
        elif sys.argv[1] == 'family':
            # 빠른 가족 설정
            quick_setup_family()
        elif sys.argv[1] == 'list':
            # 사용자 목록
            manager = UserManager()
            manager.list_users()
            manager.close()
    else:
        print("\n사용법:")
        print("  python user_manager.py setup   # 대화형 설정")
        print("  python user_manager.py family  # 빠른 가족 설정")
        print("  python user_manager.py list    # 사용자 목록")


