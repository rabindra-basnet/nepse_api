from ..core.apis import api_dict
from retrying import retry
import requests
from datetime import datetime, date
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
import json

ROOT_URL = 'https://www.nepalstock.com'



class PayloadParser():
    def __init__(self):
        self.dummyData = [147, 117, 239, 143, 157, 312, 161, 612, 512, 804, 411, 527, 170, 511, 421, 667, 764, 621, 301, 106, 133, 793, 411, 511, 312, 423, 344, 346, 653, 758, 342, 222, 236, 811, 711, 611, 122, 447, 128, 199, 183, 135, 489, 703, 800, 745, 152, 863,
                          134, 211, 142, 564, 375, 793, 212, 153, 138, 153, 648, 611, 151, 649, 318, 143, 117, 756, 119, 141, 717, 113, 112, 146, 162, 660, 693, 261, 362, 354, 251, 641, 157, 178, 631, 192, 734, 445, 192, 883, 187, 122, 591, 731, 852, 384, 565, 596, 451, 772, 624, 691]
        self.url = f"{ROOT_URL}{api_dict["marketopen_api"]["api"]}"
        self.method = api_dict["marketopen_api"]['method']
        self.payload = {}
        self.headers = {
            "authority": "www.nepalstock.com",
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.5",
            "referer": "https://www.nepalstock.com",
            "sec-ch-ua": '"Not_A Brand";v="99", "Brave";v="109", "Chromium";v="109"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        }

    def return_payload(self, access_token_value, which=None):
        headers = {
            'Authorization': f'Salter {access_token_value[0]}', **self.headers}

        response = requests.request(
            self.method, self.url, headers=headers, data=self.payload, verify=False)
        given_id = json.loads(response.content)["id"]

        today = datetime.now().day

        payload_id = self.dummyData[given_id] + given_id + 2 * today

        if which == 'stock-live':
            return payload_id

        if which == 'sector-live':
            if payload_id % 10 < 5:
                index_value = 3
            else:
                index_value = 1
        else:
            if payload_id % 10 < 5:
                index_value = 1
            else:
                index_value = 3

        payload_id = payload_id + access_token_value[1].get(
            f"salt{index_value+1}") * today - access_token_value[1].get(f"salt{index_value}")

        return payload_id
