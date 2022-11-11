import requests as rq
import datetime
import json
from tqdm import tqdm

player = {
  "ABOUT_ME": "https://www.simcompanies.com/api/v2/players/me/",
  "ACHIEVEMENTS": "https://www.simcompanies.com/api/v2/no-cache/companies/me/achievements/",
  "RESEARCH": "https://www.simcompanies.com/api/v2/players/me/research/",
  "EXECUTIVES": "https://www.simcompanies.com/api/v2/companies/me/executives/",
  "ADMIN_OVERHEAD": "https://www.simcompanies.com/api/v2/companies/me/administration-overhead/",
}

api = {
  "WAREHOUSE": "https://www.simcompanies.com/api/v2/resources/",
  "RESOURCES_ALL": "https://www.simcompanies.com/api/v3/en/encyclopedia/resources/",
  "RESOURCES_ALL_NEW": "https://www.simcompanies.com/api/v4/en/{ITEM_ID}/encyclopedia/resources/",
  "RESOURCES_SINGLE": "https://www.simcompanies.com/api/v3/en/encyclopedia/resources/{ECON_STATE}/{ITEM_ID}/",
  "RESOURCES_SINGLE_NEW": "https://www.simcompanies.com/api/v4/en/0/encyclopedia/resources/{ECON_STATE}/{ITEM_ID}/",
  "BUILDINGS": "https://www.simcompanies.com/api/v2/buildings/{ECON_STATE}/",
  "BUILDINGS_COST": "https://www.simcompanies.com/api/v2/encyclopedia/construction-cost/",
  "BUILDINGS_INFO": "https://www.simcompanies.com/api/v3/{REALM_ID}/encyclopedia/buildings/x", # change id in cookie
  "MARKET_SINGLE": "https://www.simcompanies.com/api/v2/market/{ITEM_ID}/",
  "MARKET_TICKER": "https://www.simcompanies.com/api/v1/market-ticker/" + (datetime.datetime.today() - datetime.timedelta(minutes=5)).isoformat(),
  "CONTRACTS_INCOMING": "https://www.simcompanies.com/api/v2/contracts-incoming/",
  "CONTRACTS_OUTGOING": "https://www.simcompanies.com/api/v2/contracts-outgoing/",
  "REALMS": "https://www.simcompanies.com/api/realms/"
}

econ_state = {
  "RECESSION": 0,
  "NORMAL": 1,
  "BOOM": 2
}

tax = 0.03

def main():
  """ 
  1. get resource list (api.resources_all)
  2. cache live prices (api.market_ticker)
  3. grab building info (api.buildings)
  4. foreach item, calculate:
    a. resource cost (api.resources_single.producedFrom -> api.market_ticker)
    b. wages cost (api.buildings)
    c. transport cost (api.resources_all, api.market_ticker)
    d. exchange value (api.market_ticker)
    e. production/hour
    f. profit/hour """

  ECON_STATE = 1 # NORMAL
  resource_list = rq.get(api["RESOURCES_ALL"]).json()
  live_prices = {x["kind"]:x for x in rq.get(api["MARKET_TICKER"]).json()}
  item_profits = {}
  for rs in tqdm(resource_list):
    try:
      item_data = rq.get(api["RESOURCES_SINGLE"].format(ECON_STATE=ECON_STATE, ITEM_ID=rs["db_letter"])).json()
      res_needed = item_data["producedFrom"]
      resource_cost = 0
      for item in res_needed:
        resource_cost += live_prices[item["resource"]["db_letter"]]["price"] * item["amount"]
      wage_cost = item_data["baseSalary"] / item_data["producedAnHour"]
      transport_cost = live_prices[13]["price"] * item_data["transportNeeded"] if item_data["transportNeeded"] else 0
      profit = live_prices[rs["db_letter"]]["price"] - (resource_cost + wage_cost + transport_cost + (0.03 * live_prices[rs["db_letter"]]["price"])) 
      profit_hour = profit * item_data["producedAnHour"]
      item_profits[rs["name"]] = {
        # "price": round(live_prices[rs["db_letter"]]["price"]),
        "cost": round(resource_cost + wage_cost + transport_cost + (0.03 * live_prices[rs["db_letter"]]["price"]), 2),
        "rate": round(item_data["producedAnHour"], 2),
        # "profit/item": round(profit, 2),
        "profit": round(profit_hour, 2)
      }
    except Exception as e:
      print("Exception:", e)
  item_profits = dict(sorted(item_profits.items(), key=lambda x: x[1]["profit"]))
  with open('profits.json', 'w', encoding='utf-8') as f:
    json.dump(item_profits, f, indent=2, sort_keys=False, ensure_ascii=False)


if __name__ == "__main__":
  main()