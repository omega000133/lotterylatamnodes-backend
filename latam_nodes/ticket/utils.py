import requests

def get_node_reward():
    try:
        url = "https://api-celestia.mzonder.com/cosmos/distribution/v1beta1/validators/celestiavaloper14v4ush42xewyeuuldf6jtdz0a7pxg5fwrlumwf/outstanding_rewards"
        response = requests.get(url)
        data = response.json()
        
        rewards  = data.get("rewards").get("rewards")
        # return value that denom is utia
        return float(next(item["amount"] for item in rewards if item["denom"] == "utia"))
    except Exception as e:
        print(e)
        return 0