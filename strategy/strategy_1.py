import time

from utils.get_account import get_account_information
from utils.kis import request
from utils.utils import buy_order, max_buy_qty, save_log, wait_for_open, won

BUDGET_RATIO = 0.20
MAX_BUY_COUNT = 5
UPPER_LIMIT_RATE = 29.5


def get_top_increasing_stocks():
    data = request(
        "GET",
        "/uapi/domestic-stock/v1/ranking/fluctuation",
        "FHPST01700000",
        params={
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20170",
            "fid_input_iscd": "0000",
            "fid_rank_sort_cls_code": "0",
            "fid_input_cnt_1": "0",
            "fid_prc_cls_code": "1",
            "fid_input_price_1": "",
            "fid_input_price_2": "",
            "fid_vol_cnt": "",
            "fid_trgt_cls_code": "0",
            "fid_trgt_exls_cls_code": "0",
            "fid_div_cls_code": "0",
            "fid_rsfl_rate1": "",
            "fid_rsfl_rate2": "",
        },
    )
    return data.get("output", []) if data else []


def run_strategy_1():
    print("[STRATEGY_1] 상승률 상위 분할 매수 시작")
    if not wait_for_open():
        print("[STRATEGY_1] 장 시간이 아니라 종료")
        return

    account = get_account_information()
    if not account or account["deposit"] <= 0:
        print("[STRATEGY_1] 예수금 없음")
        return

    budget = account["deposit"] * BUDGET_RATIO
    owned = {i["code"] for i in account["inventory"]}
    print(f"[STRATEGY_1] 종목당 예산 {won(budget)}")

    buy_count = 0
    for stock in get_top_increasing_stocks():
        if buy_count >= MAX_BUY_COUNT:
            break

        code = stock["stck_shrn_iscd"]
        name = stock["hts_kor_isnm"]
        price = int(stock["stck_prpr"])
        rate = float(stock["prdt_ctrt"])

        if code in owned or rate >= UPPER_LIMIT_RATE or price <= 0:
            continue

        quantity = min(int(budget // price), max_buy_qty(code))
        if quantity < 1:
            continue

        print(f"[BUY] {name}({code}) {won(price)} +{rate}% {quantity}주")
        if buy_order(code, quantity):
            buy_count += 1
            save_log(f"[BUY] {name} | {code} | 등락률:{rate:.2f}% | 현재가:{price:,}원 | 수량:{quantity}주")
        time.sleep(0.5)

    print(f"[STRATEGY_1] 완료: {buy_count}종목 매수")


if __name__ == "__main__":
    run_strategy_1()
