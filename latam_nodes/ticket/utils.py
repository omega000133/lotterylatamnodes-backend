import itertools
import random
import string

import requests


def get_node_reward():
    try:
        url = "https://api-celestia.mzonder.com/cosmos/distribution/v1beta1/validators/celestiavaloper14v4ush42xewyeuuldf6jtdz0a7pxg5fwrlumwf/commission"
        response = requests.get(url)
        data = response.json()

        rewards = data.get("commission").get("commission")
        # return value that denom is utia
        return (
            float(next(item["amount"] for item in rewards if item["denom"] == "utia"))
            / 1e6
        )
    except Exception as e:
        print(e)
        return 0


def generate_random_hash(length=4):
    characters = string.digits + string.ascii_uppercase
    hash_str = "".join(random.choices(characters, k=length))
    return hash_str


def generate_hex_hash(digits=4):
    max_value = 16 ** digits
    hex_format = f"{{:0{digits}X}}"
    hex_hashes = [hex_format.format(i) for i in range(max_value)]

    random.shuffle(hex_hashes)

    return hex_hashes
