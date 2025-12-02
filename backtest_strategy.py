"""
변동성 기반 매수 전략 백테스트
5년간 1시그마/2시그마 하락 시 매수 전략 검증
"""

import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# 한글 폰트 설정
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False


class VolatilityBacktest:
    """변동성 기반 매수 전략 백테스트"""
    
    def __init__(self, ticker, ticker_name, window=252):
        """
        Args:
            ticker: 종목 코드
            ticker_name: 종목명
            window: 표준편차 계산 윈도우 (기본: 252일 = 1년)
        """
        self.ticker = ticker
        self.ticker_name = ticker_name
        self.window = window
        self.df = None
        self.results = {}
    
    def load_data(self, years=5):
        """데이터 로드"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years*365 + 100)  # 여유있게
        
        print(f"📊 {self.ticker_name} 데이터 로딩 중...")
        print(f"   기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        
        try:
            self.df = fdr.DataReader(self.ticker, start_date, end_date)
            
            # 일일 수익률 계산
            self.df['Returns'] = self.df['Close'].pct_change() * 100
            
            # 롤링 표준편차 계산 (1년 윈도우)
            self.df['Volatility'] = self.df['Returns'].rolling(window=self.window).std()
            
            # NaN 제거
            self.df = self.df.dropna()
            
            print(f"✅ 데이터 로드 완료: {len(self.df)}일")
            return True
            
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")
            return False
    
    def run_strategy(self, amount_1sigma=1000, amount_2sigma=2000):
        """
        전략 실행
        
        Args:
            amount_1sigma: 1시그마 하락 시 매수 금액 ($)
            amount_2sigma: 2시그마 하락 시 매수 금액 ($)
        """
        print(f"\n🎯 백테스트 실행 중...")
        print(f"   • 1시그마 하락 시: ${amount_1sigma:,.0f} 매수")
        print(f"   • 2시그마 하락 시: ${amount_2sigma:,.0f} 매수")
        
        # 전략 초기화
        cash = 0  # 사용한 현금
        shares = 0  # 보유 주식 수
        portfolio_value = []
        buy_signals = []
        
        # 매수 카운터
        buy_1sigma_count = 0
        buy_2sigma_count = 0
        
        # 각 날짜별로 전략 실행
        for idx, row in self.df.iterrows():
            returns = row['Returns']
            volatility = row['Volatility']
            price = row['Close']
            
            # 매수 신호 확인
            if returns <= -2 * volatility:  # 2시그마 이상 하락
                shares_to_buy = amount_2sigma / price
                shares += shares_to_buy
                cash += amount_2sigma
                buy_2sigma_count += 1
                buy_signals.append({
                    'date': idx,
                    'type': '2sigma',
                    'price': price,
                    'returns': returns,
                    'volatility': volatility,
                    'amount': amount_2sigma
                })
                
            elif returns <= -volatility:  # 1시그마 이상 하락
                shares_to_buy = amount_1sigma / price
                shares += shares_to_buy
                cash += amount_1sigma
                buy_1sigma_count += 1
                buy_signals.append({
                    'date': idx,
                    'type': '1sigma',
                    'price': price,
                    'returns': returns,
                    'volatility': volatility,
                    'amount': amount_1sigma
                })
            
            # 현재 포트폴리오 가치
            portfolio_value.append(shares * price)
        
        # 최종 결과
        final_price = self.df['Close'].iloc[-1]
        final_portfolio_value = shares * final_price
        total_return = ((final_portfolio_value - cash) / cash * 100) if cash > 0 else 0
        
        # Buy and Hold 비교
        initial_price = self.df['Close'].iloc[0]
        buy_hold_shares = cash / initial_price if cash > 0 else 0
        buy_hold_value = buy_hold_shares * final_price
        buy_hold_return = ((buy_hold_value - cash) / cash * 100) if cash > 0 else 0
        
        # 결과 저장
        self.results = {
            'ticker': self.ticker,
            'ticker_name': self.ticker_name,
            'period_days': len(self.df),
            'period_years': len(self.df) / 252,
            
            # 매수 정보
            'buy_1sigma_count': buy_1sigma_count,
            'buy_2sigma_count': buy_2sigma_count,
            'total_buys': buy_1sigma_count + buy_2sigma_count,
            
            # 투자 금액
            'total_invested': cash,
            'final_shares': shares,
            
            # 전략 수익
            'final_price': final_price,
            'final_value': final_portfolio_value,
            'total_profit': final_portfolio_value - cash,
            'total_return_pct': total_return,
            
            # Buy and Hold 비교
            'buy_hold_shares': buy_hold_shares,
            'buy_hold_value': buy_hold_value,
            'buy_hold_profit': buy_hold_value - cash,
            'buy_hold_return_pct': buy_hold_return,
            
            # 성과 차이
            'outperformance': total_return - buy_hold_return,
            
            # 상세 데이터
            'buy_signals': buy_signals,
            'portfolio_values': portfolio_value,
            'initial_price': initial_price
        }
        
        return self.results
    
    def print_results(self):
        """결과 출력"""
        r = self.results
        
        print(f"\n{'='*70}")
        print(f"📊 {r['ticker_name']} ({r['ticker']}) 백테스트 결과")
        print(f"{'='*70}")
        
        print(f"\n📅 분석 기간:")
        print(f"   • 거래일: {r['period_days']:,}일 ({r['period_years']:.1f}년)")
        
        print(f"\n💰 매수 내역:")
        print(f"   • 1시그마 매수: {r['buy_1sigma_count']:,}회")
        print(f"   • 2시그마 매수: {r['buy_2sigma_count']:,}회")
        print(f"   • 총 매수: {r['total_buys']:,}회")
        print(f"   • 총 투자금: ${r['total_invested']:,.2f}")
        print(f"   • 매수 주식: {r['final_shares']:,.2f}주")
        
        print(f"\n📈 전략 성과:")
        print(f"   • 최종 가격: ${r['final_price']:,.2f}")
        print(f"   • 최종 가치: ${r['final_value']:,.2f}")
        print(f"   • 순이익: ${r['total_profit']:,.2f}")
        print(f"   • 수익률: {r['total_return_pct']:+.2f}%")
        
        print(f"\n📊 Buy & Hold 비교:")
        print(f"   • 초기 가격: ${r['initial_price']:,.2f}")
        print(f"   • 매수 주식: {r['buy_hold_shares']:,.2f}주")
        print(f"   • 최종 가치: ${r['buy_hold_value']:,.2f}")
        print(f"   • 순이익: ${r['buy_hold_profit']:,.2f}")
        print(f"   • 수익률: {r['buy_hold_return_pct']:+.2f}%")
        
        print(f"\n⚡ 성과 차이:")
        diff = r['outperformance']
        symbol = "🟢" if diff > 0 else "🔴" if diff < 0 else "⚪"
        print(f"   {symbol} 전략 - Buy&Hold: {diff:+.2f}%p")
        
        if diff > 0:
            print(f"   ✅ 전략이 Buy & Hold보다 우수합니다!")
        elif diff < 0:
            print(f"   ❌ Buy & Hold가 전략보다 우수합니다.")
        else:
            print(f"   ⚪ 동일한 성과입니다.")
    
    def visualize(self, save_path=None):
        """결과 시각화"""
        r = self.results
        
        fig, axes = plt.subplots(3, 1, figsize=(14, 12))
        
        # 그래프 1: 가격 차트 + 매수 신호
        ax1 = axes[0]
        ax1.plot(self.df.index, self.df['Close'], 'b-', linewidth=1.5, label='가격', alpha=0.7)
        
        # 매수 신호 표시
        buy_1sigma = [b for b in r['buy_signals'] if b['type'] == '1sigma']
        buy_2sigma = [b for b in r['buy_signals'] if b['type'] == '2sigma']
        
        if buy_1sigma:
            dates_1 = [b['date'] for b in buy_1sigma]
            prices_1 = [b['price'] for b in buy_1sigma]
            ax1.scatter(dates_1, prices_1, c='orange', s=50, marker='^', 
                       label=f'1σ 매수 ({len(buy_1sigma)}회)', zorder=5)
        
        if buy_2sigma:
            dates_2 = [b['date'] for b in buy_2sigma]
            prices_2 = [b['price'] for b in buy_2sigma]
            ax1.scatter(dates_2, prices_2, c='red', s=100, marker='^',
                       label=f'2σ 매수 ({len(buy_2sigma)}회)', zorder=5)
        
        ax1.set_title(f'{r["ticker_name"]} - 가격 차트 & 매수 시점', fontsize=14, fontweight='bold')
        ax1.set_xlabel('날짜', fontsize=12)
        ax1.set_ylabel('가격 ($)', fontsize=12)
        ax1.legend(loc='best', fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # 그래프 2: 포트폴리오 가치 변화
        ax2 = axes[1]
        ax2.plot(self.df.index, r['portfolio_values'], 'g-', linewidth=2, label='전략 포트폴리오')
        
        # Buy & Hold 포트폴리오 계산
        buy_hold_values = [r['buy_hold_shares'] * price for price in self.df['Close']]
        ax2.plot(self.df.index, buy_hold_values, 'b--', linewidth=2, label='Buy & Hold', alpha=0.7)
        
        # 투자금 라인
        ax2.axhline(y=r['total_invested'], color='gray', linestyle=':', linewidth=2, 
                   label=f'투자금: ${r["total_invested"]:,.0f}', alpha=0.5)
        
        ax2.set_title('포트폴리오 가치 비교', fontsize=14, fontweight='bold')
        ax2.set_xlabel('날짜', fontsize=12)
        ax2.set_ylabel('가치 ($)', fontsize=12)
        ax2.legend(loc='best', fontsize=10)
        ax2.grid(True, alpha=0.3)
        
        # 그래프 3: 누적 수익률
        ax3 = axes[2]
        
        strategy_returns = [(v - r['total_invested']) / r['total_invested'] * 100 
                           for v in r['portfolio_values']]
        buy_hold_returns = [(v - r['total_invested']) / r['total_invested'] * 100 
                           for v in buy_hold_values]
        
        ax3.plot(self.df.index, strategy_returns, 'g-', linewidth=2, label='전략 수익률')
        ax3.plot(self.df.index, buy_hold_returns, 'b--', linewidth=2, label='Buy & Hold 수익률', alpha=0.7)
        ax3.axhline(y=0, color='gray', linestyle='-', linewidth=1, alpha=0.5)
        
        ax3.set_title('누적 수익률 비교', fontsize=14, fontweight='bold')
        ax3.set_xlabel('날짜', fontsize=12)
        ax3.set_ylabel('수익률 (%)', fontsize=12)
        ax3.legend(loc='best', fontsize=10)
        ax3.grid(True, alpha=0.3)
        
        # 통계 정보 박스
        textstr = f'전략: {r["total_return_pct"]:+.1f}%\n'
        textstr += f'Buy&Hold: {r["buy_hold_return_pct"]:+.1f}%\n'
        textstr += f'차이: {r["outperformance"]:+.1f}%p'
        
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
        ax3.text(0.02, 0.98, textstr, transform=ax3.transAxes, fontsize=11,
                verticalalignment='top', bbox=props)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"\n📊 차트 저장: {save_path}")
        
        plt.show()


def compare_strategies(results_list):
    """여러 종목 전략 비교"""
    print("\n" + "="*70)
    print("📊 전체 종목 비교")
    print("="*70)
    
    print(f"\n{'종목':<20} {'매수횟수':<12} {'전략수익률':<15} {'B&H수익률':<15} {'차이':<10}")
    print("-"*70)
    
    for r in results_list:
        name = r['ticker_name'][:18]
        buys = r['total_buys']
        strategy = r['total_return_pct']
        buy_hold = r['buy_hold_return_pct']
        diff = r['outperformance']
        
        symbol = "🟢" if diff > 0 else "🔴" if diff < 0 else "⚪"
        
        print(f"{name:<20} {buys:>4}회      "
              f"{strategy:>6.1f}%        "
              f"{buy_hold:>6.1f}%        "
              f"{symbol} {diff:>+6.1f}%p")


def main():
    """메인 실행"""
    print("\n" + "="*70)
    print("🎯 5년 백테스트: 변동성 기반 매수 전략")
    print("="*70)
    
    # 분석 종목
    stocks = [
        ('QLD', 'ProShares Ultra QQQ'),
        ('TQQQ', 'ProShares UltraPro QQQ'),
        ('SOXL', 'Direxion Daily Semiconductor Bull 3X'),
    ]
    
    # 매수 금액 설정
    amount_1sigma = 1000  # $1,000
    amount_2sigma = 2000  # $2,000
    
    print(f"\n💵 매수 금액:")
    print(f"   • 1시그마 하락 시: ${amount_1sigma:,}")
    print(f"   • 2시그마 하락 시: ${amount_2sigma:,}")
    
    # 각 종목 백테스트
    all_results = []
    
    for ticker, name in stocks:
        print(f"\n{'='*70}")
        
        # 백테스트 실행
        bt = VolatilityBacktest(ticker, name, window=252)
        
        if bt.load_data(years=5):
            results = bt.run_strategy(amount_1sigma, amount_2sigma)
            bt.print_results()
            
            # 차트 생성
            save_path = f"{ticker}_{name.replace(' ', '_')}_backtest.png"
            bt.visualize(save_path)
            
            all_results.append(results)
        
        print()
    
    # 전체 비교
    if all_results:
        compare_strategies(all_results)
    
    print("\n✅ 백테스트 완료!")


if __name__ == "__main__":
    main()



