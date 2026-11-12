from utils.kis import ACNT_PRDT_CD, CANO, IS_SIMULATION, TR_PREFIX, request
from utils.utils import won


def get_account_information(verbose=True):
    data = request(
        "GET",
        "/uapi/domestic-stock/v1/trading/inquire-balance",
        f"{TR_PREFIX}TTC8434R",
        params={
            "CANO": CANO,
            "ACNT_PRDT_CD": ACNT_PRDT_CD,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        },
    )
    if not data:
        return None

    summary = data["output2"][0]
    deposit = int(summary["prvs_rcdl_excc_amt"])
    inventory = [
        {
            "name": s["prdt_name"],
            "code": s["pdno"],
            "buy_price": float(s["pchs_avg_pric"]),
            "current_price": int(s["prpr"]),
            "rate": float(s["evlu_erng_rt"]),
            "quantity": int(s["hldg_qty"]),
            "sellable": int(s["ord_psbl_qty"]),
        }
        for s in data.get("output1", [])
        if s.get("pdno") and int(s.get("hldg_qty", 0)) > 0
    ]

    if verbose:
        env = "모의투자" if IS_SIMULATION else "실전투자"
        print(f"[{env}] 예수금(D+2) {won(deposit)} | 총평가 {won(summary['tot_evlu_amt'])}")
        for i in inventory:
            print(
                f"  {i['name'][:8]:<10} {i['code']} 매입 {won(i['buy_price'])} "
                f"현재 {won(i['current_price'])} {i['quantity']}주 {i['rate']:.2f}%"
            )

    return {"deposit": deposit, "inventory": inventory}


if __name__ == "__main__":
    get_account_information()
