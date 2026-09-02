import requests
import json
import os
from auth import (
    URL_BASE, APP_KEY, APP_SECRET, get_access_token, 
    CANO, ACNT_PRDT_CD, IS_SIMULATION 
)
from utils import format_currency

def get_account_information():
    """
    [기능] 예수금, 보유 종목 상세 정보 반환 (TR ID 직접 지정 방식)
    """
    path = "/uapi/domestic-stock/v1/trading/inquire-balance"
    url = f"{URL_BASE}{path}"

    # ✅ TR ID를 외부에서 들고오지 않고, 내부에서 직접 분기 처리
    # 실전: TTTC8434R / 모의: VTTC8434R
    current_tr_id = "VTTC8434R" if IS_SIMULATION else "TTTC8434R"

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "authorization": f"Bearer {get_access_token()}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": current_tr_id, # 직접 결정된 ID 사용
        "custtype": "P",
    }

    # 파라미터 설정 (이전에 성공했던 필수 필드들)
    params = {
        "CANO": CANO,                   # 계좌번호 앞 8자리
        "ACNT_PRDT_CD": ACNT_PRDT_CD,   # 계좌번호 뒤 2자리
        "AFHR_FLPR_YN": "N",            # 시간외단일가여부
        "OVRSR_DR_EVL_PFT_FLG_YN": "N", # 해외주식평가손익구분여부
        "PRDT_DVSN_CD": "01",           # 상품구분코드 (01: 주식)
        "UNPR_DVSN_CD": "01",           # 단가구분코드
        "UNPR_DVSN": "01",
        "CTX_AREA_FK100": "",           # 연속조회검색조건1
        "CTX_AREA_NK100": "",           # 연속조회검색조건2
        "INQR_DVSN": "02",              # 조회구분 (01: 대출금포함, 02: 종목별)
        "OFL_YN": "N",                  # ✅ 오프라인여부 (에러 발생 지점: 'N'으로 설정)
        "FUND_STTL_ICLD_YN": "N",       # 펀드결제포함여부
        "FNCG_AMT_AUTO_RDPT_YN": "N",   # 융자금액자동상환여부
        "PRCS_DVSN": "00"               # 처리구분 (00: 전일포함, 01: 당일만)
    }

    try:
        res = requests.get(url, headers=headers, params=params)
        data = res.json()

        if data.get('rt_cd') != '0':
            print(f"❌ 계좌 정보 조회 실패: {data.get('msg1')}")
            return None

        # 1. 예수금 및 자산 요약
        summary = data['output2'][0]
        deposit = int(summary['dnca_tot_amt'])
        total_evlu = int(summary['tot_evlu_amt'])

        env_label = "모의투자" if IS_SIMULATION else "실전투자"
        print("\n" + "="*65)
        print(f"💰 [{env_label} 계좌 요약]")
        print(f"예수금: {format_currency(deposit)} | 총 자산: {format_currency(total_evlu)}")
        print("="*65)

        # 2. 보유 종목 리스트
        stocks = data.get('output1', [])
        inventory = []

        if not stocks or (len(stocks) == 1 and stocks[0]['pdno'] == ''):
            print("보유 중인 종목이 없습니다.")
        else:
            print(f"{'종목명':<11} | {'코드':<7} | {'구매가':>11} | {'보유수량':>6} | {'현재가':>11} | {'수익률':>7}")
            print("-" * 65)

        for s in stocks:
           if s['pdno'] == '': continue

           # 1. 종목명 필드 수정 (prdt_name -> prdt_nm)
           name = s.get('prdt_name', '이름없음')

           code = s['pdno']

           # 2. 숫자형 데이터 변환 (안전하게 처리)
           buy_price = int(float(s['pchs_avg_pric']))
           current_price = int(s['prpr'])
           qty = int(s.get('hldg_qty',0))
           # 3. 수익률 소수점 제한 (예: 0.75%)
           rate = float(s['evlu_erng_rt'])
           formatted_rate = f"{rate:.2f}%"

           # 출력 부분
           print(f"{name[:8]:<12} | {code:<8} | {format_currency(buy_price):>12} | {qty:>6} | {format_currency(current_price):>12} | {formatted_rate:>8}")

           inventory.append({
                "name": name,
                "code": code,
                "buy_price": buy_price,
                "current_price": current_price,
                "rate": rate,
		"quantity": qty
            })

        print("="*65 + "\n")
        return {"deposit": deposit, "inventory": inventory}

    except Exception as e:
        print(f"시스템 에러 발생: {e}")
        return None

if __name__ == "__main__":
    get_account_information()
