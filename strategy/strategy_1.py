import time
import requests
from auth import URL_BASE, APP_KEY, APP_SECRET, get_access_token
from utils import save_log, is_market_open, buy_order, format_currency
from get_deposit import get_deposit
from get_account import get_account_information

def get_top_increasing_stocks():
    """
    [기능] 실시간 상승률 상위 종목 조회 (누락된 파라미터 전체 보강)
    """
    url = f"{URL_BASE}/uapi/domestic-stock/v1/ranking/fluctuation"
    token = get_access_token()
    
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "FHPST01700000",  # 모의/실전 동일하게 사용되는 시세 TR ID
        "custtype": "P"
    }
    
    # 💡 에러 원인 해결: 한국투자증권 API 명세 기준 필수 파라미터 전면 추가
    params = {
        "fid_rsfl_rate2": "",             # 등락률2 (빈 값)
        "fid_cond_mrkt_div_code": "J",    # 시장구분 (J: 주식)
        "fid_cond_scr_div_code": "20170", # 화면구분코드
        "fid_input_iscd": "0000",         # 입력종목코드 (0000: 전체)
        "fid_rank_sort_cls_code": "0",    # 순위정렬구분코드 (0: 상승률순)
        "fid_input_cnt_1": "0",           # 입력카운트1 (0: 전체)
        "fid_prc_cls_code": "1",          # 가격구분코드 (1: 현재가 기준)
        "fid_input_price_1": "",          # 가격조건 시작
        "fid_input_price_2": "",          # 가격조건 끝
        "fid_vol_cnt": "",                # 거래량 조건
        "fid_trgt_cls_code": "0",         # 타겟구분코드 (0: 전체)
        "fid_trgt_exls_cls_code": "0",    # 타겟제외구분코드 (0: 제외없음)
        "fid_div_cls_code": "0",          # 분류구분코드 (0: 전체)
        "fid_rsfl_rate1": ""              # 등락률1 (빈 값)
    }
    
    try:
        res = requests.get(url, headers=headers, params=params)
        data = res.json()
        
        if data.get('rt_cd') == '0':
            return data.get('output', [])
        else:
            print(f"❌ [API_ERROR] 상승률 조회 실패: {data.get('msg1')}")
            return []
    except Exception as e:
        print(f"❌ [SYSTEM_ERROR] 상승률 조회 중 예외 발생: {e}")
        return []

def run_strategy_1():
    print("\n" + "="*65)
    print("🚀 [STRATEGY_1] 실시간 상승률 상위 분할 매수 전략 실행")
    print("="*65)
    
    # 1. 장 시간 체크
    if not is_market_open():
        print("🛑 장 시간이 아니므로 전략을 종료합니다.")
        return
        
    # 2. 예수금 조회
    deposit = get_deposit()
    if deposit <= 0:
        print("❌ 매수 가능한 예수금이 부족합니다.")
        return
        
    # 3. 분할 매수 금액 설정 (총 예수금의 20%)
    budget_per_stock = deposit * 0.20
    print(f"💰 총 예수금: {format_currency(deposit)}")
    print(f"🎯 종목당 매수 할당 금액: {format_currency(budget_per_stock)}")
    print("-" * 65)
    
    # 4. 현재 보유 종목 확인 (중복 매수 필터링용)
    account_info = get_account_information()
    owned_codes = []
    if account_info and 'inventory' in account_info:
        owned_codes = [item['code'] for item in account_info['inventory']]
        
    # 5. 실시간 상승률 TOP 종목 조회
    top_stocks = get_top_increasing_stocks()
    if not top_stocks:
        print("❌ 매수 대상 종목을 찾지 못했습니다.")
        return
        
    buy_count = 0
    max_buy_count = 5 # 최대 5종목 제한
    
    for stock in top_stocks:
        if buy_count >= max_buy_count:
            break
            
        code = stock['stck_shrn_iscd']
        name = stock['hts_kor_isnm']
        current_price = int(stock['stck_prpr'])
        fluctuation_rate = float(stock['prdy_ctrt'])
        
        # [제외조건 1] 이미 보유 중인 종목
        if code in owned_codes:
            print(f"⏩ [SKIP] {name}({code}) - 보유 중")
            continue
            
        # [제외조건 2] 상한가 종목 (통상적으로 29.5% 이상을 상한가 도달 위험으로 간주)
        if fluctuation_rate >= 29.5:
            print(f"⏩ [SKIP] {name}({code}) - 상한가 도달 위험 ({fluctuation_rate}%)")
            continue
            
        # [제외조건 3] 매수 수량 1주 미만
        quantity = int(budget_per_stock // current_price)
        if quantity < 1:
            print(f"⏩ [SKIP] {name}({code}) - 매수 금액 부족 (현재가: {format_currency(current_price)})")
            continue
            
        # 6. 시장가 매수 실행
        print(f"\n💡 [BUY_TARGET] {name}({code}) | 현재가: {format_currency(current_price)} | 상승률: {fluctuation_rate}% | 목표수량: {quantity}주")
        success = buy_order(code, quantity)
	time.sleep(1.2)
        
        if success:
            buy_count += 1
            # 7. 매수 시 로그 기록
            log_msg = (
		f"[BUY] "
  		f"{name:<10} | "
   		f"{code:<6} | "
  		f"등락률:{fluctuation_rate:>6.2f}% | "
	  	f"현재가:{current_price:>8,}원 | "
  	 	f"수량:{quantity:>5}주"
	    )
            save_log(log_msg)
            
    print("="*65)
    print(f"✅ [STRATEGY_1] 매수 프로세스 완료 (총 {buy_count}개 종목 매수). 루프를 종료합니다.")
    print("="*65)

if __name__ == "__main__":
    run_strategy_1()

