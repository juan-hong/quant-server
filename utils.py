import datetime
import pytz
import time
import requests
import json
from auth import URL_BASE, APP_KEY, APP_SECRET, get_access_token, IS_SIMULATION, CANO, ACNT_PRDT_CD

def get_now_kst():
    """
    [기능] 한국 시간(KST) 기준 현재 시각 객체를 반환
    [출력] 현재 서버 시간과 변환된 한국 시간을 비교 출력
    """
    try:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        kst_timezone = pytz.timezone('Asia/Seoul')
        now_kst = now_utc.astimezone(kst_timezone)
        
        # 초 단위까지만 깔끔하게 출력
        print(f"🕒 [TIME_CHECK] KST: {now_kst.strftime('%Y-%m-%d %H:%M:%S')}")
        return now_kst
    except Exception as e:
        print(f"❌ [TIME_ERROR] 시간 획득 실패: {e}")
        return datetime.datetime.now() # 예외 시 서버 시간이라도 반환

def is_market_open():
    """
    [기능] 현재 시점이 정규장(09:00~15:30) 운영 범위 내인지 판별
    [출력] 주말 여부, 장 개장 전/중/후 상태를 명확히 표시
    """
    now = get_now_kst()
    
    # 1. 주말 체크
    if now.weekday() >= 5:
        weekday_name = "토요일" if now.weekday() == 5 else "일요일"
        print(f"😴 [MARKET_STATUS] 오늘은 {weekday_name}로 휴장일입니다.")
        return False
        
    # 2. 시간 범위 설정
    start_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    # 3. 상태 판별
    if now < start_time:
        print(f"⏳ [MARKET_STATUS] 장 개장 전입니다. (개장까지 {start_time - now} 남음)")
        return False
    elif now > end_time:
        print(f"🌑 [MARKET_STATUS] 장이 종료되었습니다. (종료된 지 {now - end_time} 지남)")
        return False
    else:
        print(f"🚀 [MARKET_STATUS] 정규장 운영 중입니다.")
        return True

def wait_until(h, m, s):
    """
    [기능] 특정 시각(시, 분, 초)이 될 때까지 프로그램을 대기시킴
    [출력] 대기 시작 시간과 목표 시간, 남은 시간을 초 단위로 실시간 안내
    """
    target_time_str = f"{h:02d}:{m:02d}:{s:02d}"
    print(f"📡 [WAIT] 목표 시간 {target_time_str}까지 대기를 시작합니다.")
    
    while True:
        now = get_now_kst()
        target = now.replace(hour=h, minute=m, second=s, microsecond=0)
        
        # 이미 시간이 지난 경우 처리
        if now >= target:
            print(f"✅ [WAIT_SUCCESS] 목표 시간 {target_time_str}에 도달하여 대기를 종료합니다.")
            break
            
        diff = (target - now).total_seconds()
        
        # 남은 시간에 따라 출력 빈도 조절 (유연한 대기)
        if diff > 10:
            print(f"💤 [WAITING] 목표까지 {int(diff)}초 남았습니다... (30초 대기 루프)")
            time.sleep(30)
        else:
            print(f"🔥 [WAITING] 목표 임박! {round(diff, 1)}초 전...")
            time.sleep(0.5)

def format_currency(amount):
    """
    [기능] 숫자를 천 단위 콤마가 포함된 금액 형식 문자열로 변환
    [출력] 변환된 결과값 출력 (디버깅용)
    """
    try:
        formatted = format(int(amount), ',') + "원"
        # 필요 시 출력 (너무 잦으면 주석 처리 가능)
        # print(f"💰 [FORMAT] {amount} -> {formatted}")
        return formatted
    except Exception:
        return str(amount)

def get_current_price(code):
    """
    [기능] 종목코드(6자리)를 입력받아 현재가를 반환
    [출력] 종목코드와 조회된 현재가, 또는 실패 메시지
    """
    url = f"{URL_BASE}/uapi/domestic-stock/v1/quotations/inquire-price"
    token = get_access_token()
    
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "FHKST01010100"  # 주식현재가 시세 조회 ID
    }
    
    params = {
        "fid_cond_mrkt_div_code": "J", # 주식시장 분류 (J: 주식)
        "fid_input_iscd": code          # 종목코드
    }

    try:
        res = requests.get(url, headers=headers, params=params)
        data = res.json()
        
        if data.get('rt_cd') == '0':
            current_price = int(data['output']['stck_prpr'])
            print(f"📈 [PRICE_CHECK] 종목코드: {code} | 현재가: {format(current_price, ',')}원")
            return current_price
        else:
            print(f"❌ [PRICE_ERROR] {code} 조회 실패: {data.get('msg1')}")
            return None
            
    except Exception as e:
        print(f"❌ [SYSTEM_ERROR] 현재가 호출 중 서버 에러 발생: {e}")
        return None

def buy_order(code, quantity):
    """
    [기능] 국내 주식 시장가 매수 주문
    [출력] 주문 성공 여부 및 주문 상세 내역
    """
    path = "/uapi/domestic-stock/v1/trading/order-cash"
    url = f"{URL_BASE}{path}"
    
    # 모의투자(VTTC0802U)와 실전투자(TTTC0802U) ID 구분
    tr_id = "VTTC0802U" if IS_SIMULATION else "TTTC0802U"
    
    data = {
        "CANO": CANO,                       # 계좌번호 앞 8자리
        "ACNT_PRDT_CD": ACNT_PRDT_CD,       # 계좌번호 뒤 2자리
        "PDNO": str(code).zfill(6),         # 종목코드 6자리
        "ORD_DVSN": "01",                   # 주문방법 (01: 시장가)
        "ORD_QTY": str(int(quantity)),      # 주문 수량
        "ORD_UNPR": "0",                    # 시장가는 가격 0으로 세팅
    }
    
    token = get_access_token()  # 함수를 호출해서 토큰을 받아옵니다.

    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P"                     # 개인 고객
    }

    try:
        res = requests.post(url, headers=headers, data=json.dumps(data))
        res_data = res.json()
        
        if res_data.get('rt_cd') == '0':
            print(f"✅ [BUY_SUCCESS] 종목코드: {code} | 수량: {quantity}주 주문 완료")
            return True
        else:
            print(f"❌ [BUY_ERROR] 주문 실패: {res_data.get('msg1')}")
            return False
    except Exception as e:
        print(f"❌ [SYSTEM_ERROR] 매수 주문 중 에러 발생: {e}")
        return False

def sell_order(code, quantity):
    """
    [기능] 국내 주식 시장가 매도 주문
    [출력] 주문 성공 여부 및 주문 상세 내역
    """
    path = "/uapi/domestic-stock/v1/trading/order-cash"
    url = f"{URL_BASE}{path}"
    
    # 모의투자(VTTC0801U)와 실전투자(TTTC0801U) ID 구분 (매도는 ID가 다름)
    tr_id = "VTTC0801U" if IS_SIMULATION else "TTTC0801U"
    
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": str(code).zfill(6),
        "ORD_DVSN": "01",                   # 시장가 매도
        "ORD_QTY": str(int(quantity)),
        "ORD_UNPR": "0",
    }

    token = get_access_token()

    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P"
    }

    try:
        res = requests.post(url, headers=headers, data=json.dumps(data))
        res_data = res.json()
        
        if res_data.get('rt_cd') == '0':
            print(f"✅ [SELL_SUCCESS] 종목코드: {code} | 수량: {quantity}주 매도 완료")
            return True
        else:
            print(f"❌ [SELL_ERROR] 매도 실패: {res_data.get('msg1')}")
            return False
    except Exception as e:
        print(f"❌ [SYSTEM_ERROR] 매도 주문 중 에러 발생: {e}")
        return False

def save_log(message):
    """
    [기능] 매매 결정 근거를 trade_history.log 파일에 기록
    """
    try:
        now = get_now_kst()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        
        # 'a' 모드는 append(추가)입니다. 파일이 없으면 새로 만들고, 있으면 아래에 덧붙입니다.
        with open("trade_history.log", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
            
    except Exception as e:
        print(f"❌ [LOG_ERROR] 로그 기록 실패: {e}")

