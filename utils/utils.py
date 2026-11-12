import datetime
import time

from utils.kis import ACNT_PRDT_CD, CANO, ROOT, TR_PREFIX, request

KST = datetime.timezone(datetime.timedelta(hours=9))
MARKET_OPEN = datetime.time(9, 0)
MARKET_CLOSE = datetime.time(15, 30)
LOG_FILE = ROOT / "logs" / "trade_history.log"


def now_kst():
    return datetime.datetime.now(KST)


def is_market_open():
    now = now_kst()
    return now.weekday() < 5 and MARKET_OPEN <= now.time() <= MARKET_CLOSE


def wait_for_open():
    now = now_kst()
    if now.weekday() >= 5 or now.time() > MARKET_CLOSE:
        return False
    if now.time() < MARKET_OPEN:
        target = now.replace(hour=MARKET_OPEN.hour, minute=MARKET_OPEN.minute, second=0, microsecond=0)
        time.sleep((target - now).total_seconds())
    return True


def won(amount):
    return f"{int(amount):,}원"


def get_current_price(code):
    data = request(
        "GET",
        "/uapi/domestic-stock/v1/quotations/inquire-price",
        "FHKST01010100",
        params={"fid_cond_mrkt_div_code": "J", "fid_input_iscd": code},
    )
    return int(data["output"]["stck_prpr"]) if data else None


def max_buy_qty(code):
    data = request(
        "GET",
        "/uapi/domestic-stock/v1/trading/inquire-psbl-order",
        f"{TR_PREFIX}TTC8908R",
        params={
            "CANO": CANO,
            "ACNT_PRDT_CD": ACNT_PRDT_CD,
            "PDNO": code,
            "ORD_UNPR": "0",
            "ORD_DVSN": "01",
            "CMA_EVLU_AMT_ICLD_YN": "N",
            "OVRS_ICLD_YN": "N",
        },
    )
    return int(data["output"]["nrcvb_buy_qty"]) if data else 0


def _order(tr_id, code, quantity):
    data = request(
        "POST",
        "/uapi/domestic-stock/v1/trading/order-cash",
        tr_id,
        body={
            "CANO": CANO,
            "ACNT_PRDT_CD": ACNT_PRDT_CD,
            "PDNO": str(code).zfill(6),
            "ORD_DVSN": "01",
            "ORD_QTY": str(int(quantity)),
            "ORD_UNPR": "0",
        },
    )
    return data is not None


def buy_order(code, quantity):
    return _order(f"{TR_PREFIX}TTC0802U", code, quantity)


def sell_order(code, quantity):
    return _order(f"{TR_PREFIX}TTC0801U", code, quantity)


def save_log(message):
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{now_kst():%Y-%m-%d %H:%M:%S}] {message}\n")
