# quant-server-backup

한국투자증권 Open API 자동매매 서버 백업.

## 설정

`private/auth.py` (git 제외):

```python
IS_SIMULATION = True

SIM = {"URL_BASE": "...", "APP_KEY": "...", "APP_SECRET": "...", "CANO": "...", "ACNT_PRDT_CD": "01"}
REAL = {"URL_BASE": "...", "APP_KEY": "...", "APP_SECRET": "...", "CANO": "...", "ACNT_PRDT_CD": "01"}
```

```bash
pip install -r requirements.txt
```

## 실행

저장소 루트에서 실행한다.

```bash
python -m utils.get_account
python -m strategy.strategy_1
python -m strategy.stoploss_1
```

## cron 예시 (서버 시간대 KST 기준)

```
55 8 * * 1-5 cd /home/USER/quant-server && python3 -m strategy.stoploss_1 >> logs/stoploss.log 2>&1
0 10 * * 1-5 cd /home/USER/quant-server && python3 -m strategy.strategy_1 >> logs/strategy.log 2>&1
```
