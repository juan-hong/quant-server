import time
import requests
from auth import URL_BASE, APP_KEY, APP_SECRET, get_access_token, CANO, ACNT_PRDT_CD, IS_SIMULATION, PARAMS_BALANCE
from utils import save_log, is_market_open, get_current_price, sell_order
from get_account import get_account_information

def run_stoploss():
    print("\n" + "="*65)
    print("🛡️ [STOPLOSS_1] 보유 종목 실시간 손절(-2%) 모니터링 시작")
    print("="*65)
    
    # 8. 장 종료 시 자동 종료
    while True:
        if not is_market_open():
            print("🛑 장이 종료되었으므로 손절 감시 모니터링을 종료합니다.")
            break
            
        print("\n🔍 [CHECK] 보유 종목 손익률 점검 중...")
        
        # 1. get_account_information() 호출 및 inventory 확보
        account_info = get_account_information()
        if not account_info or not account_info.get('inventory'):
            print("📭 현재 보유 중인 종목이 없습니다. 30초 대기...")
            time.sleep(30)
            continue
            
        inventory = account_info['inventory']
        
        # 2. 보유 종목 반복문
        for item in inventory:
            code = item['code']
            name = item['name']
            buy_price = item['buy_price']
	    quantity = item["quantity"]
            
            # 3. 현재가 실시간 조회
            current_price = get_current_price(code)
            if current_price is None:
                continue
                
            # 4. 손익률 계산 공식 적용
            yield_rate = ((current_price - buy_price) / buy_price) * 100
            print(f"📊 {name}({code}) | 구매가: {buy_price}원 | 현재가: {current_price}원 | 실시간 수익률: {yield_rate:.2f}%")
            
            # 5. 조건: -2% 도달 시 즉시 매도
            if yield_rate <= -2.0:
                print(f"🚨 [STOPLOSS_TRIGGER] {name} 손절 조건(-2%) 충족! 전량 매도를 시도합니다.")
                
                if quantity > 0:
                    # 6. 즉시 시장가 매도
                    success = sell_order(code, quantity)
                    
                    if success:
                        # 7. 매도 성공 시 로그 기록
                        log_msg = (
			     f"[STOPLOSS] "
 			     f"종목:{name} | "
 			     f"코드:{code} | "
 			     f"매수가:{buy_price:,}원 | "
 			     f"현재가:{current_price:,}원 | "
 			     f"수익률:{yield_rate:.2f}%"
			)
                        save_log(log_msg)
                        print(f"✅ {name} 손절 완료 및 로그 저장 성공.")
                else:
                    print(f"⚠️ [SYSTEM_WARN] {name}의 보유 수량을 확인할 수 없어 주문이 스킵되었습니다.")
            
            # 9. API 호출 제한(초당 N건)을 방지하기 위한 유휴 시간 확보
            time.sleep(0.5)
            
        print("💤 1사이클 점검이 완료되었습니다. 15초 후 재점검합니다...")
        time.sleep(15)

if __name__ == "__main__":
    run_stoploss()
