import os
import requests
from auth import (
    get_access_token, APP_KEY, APP_SECRET, URL_BASE, CANO, ACNT_PRDT_CD, PARAMS_BALANCE, IS_SIMULATION
)

def get_deposit():
    token = get_access_token()
    url = f"{URL_BASE}/uapi/domestic-stock/v1/trading/inquire-balance"
    tr_id = "VTTC8434R" if IS_SIMULATION else "TTTC8434R"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
	"tr_id" : tr_id
    }
    
    # 공통 필드와 환경별 특화 필드를 합칩니다.
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "AFHR_FLPR_YN": "N",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
        **PARAMS_BALANCE  # auth에서 정의한 환경별 파라미터를 언패킹(합치기)
    }

    try:
        res = requests.get(url, headers=headers, params=params)
        
        if res.status_code == 401:
            if os.path.exists("token.dat"):
                os.remove("token.dat")
            return get_deposit()

        data = res.json()
        if data.get('rt_cd') == '0':
            # 주문가능금액 반환
            return int(data['output2'][0]['dnca_tot_amt'])
        else:
            print(f"❌ API 오류: {data.get('msg1')}")
            return 0
            
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        return 0

if __name__ == "__main__":
    cash = get_deposit()
    print(f"✅ 현재 설정된 계좌의 예수금: {format(cash, ',')}원")
