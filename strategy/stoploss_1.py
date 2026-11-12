import time

from utils.get_account import get_account_information
from utils.utils import is_market_open, save_log, sell_order, wait_for_open

STOPLOSS_RATE = -2.0
INTERVAL = 15


def run_stoploss():
    if not wait_for_open():
        return

    while is_market_open():
        account = get_account_information(verbose=False)
        for item in account["inventory"] if account else []:
            rate = (item["current_price"] - item["buy_price"]) / item["buy_price"] * 100
            if rate > STOPLOSS_RATE or item["sellable"] < 1:
                continue

            if sell_order(item["code"], item["sellable"]):
                save_log(
                    f"[STOPLOSS] 종목:{item['name']} | 코드:{item['code']} | "
                    f"매수가:{item['buy_price']:,.0f}원 | 현재가:{item['current_price']:,}원 | 수익률:{rate:.2f}%"
                )
            time.sleep(0.5)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    run_stoploss()
