from retrying import retry
import aiohttp
import asyncio
from datetime import datetime, date
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
import time
from .apis import api_dict

ROOT_URL = 'https://www.nepalstock.com'

class TokenParser:
    MEMORY = [5, 8, 4, 7, 9, 4, 6, 9, 5, 5, 6, 5, 3, 5, 4, 4, 9, 6, 6, 8, 8, 6, 8, 6, 5, 8, 4, 9, 5, 9, 8, 5, 3, 4, 7, 7, 4, 7, 3, 9]

    def cdx(self, salt1, salt2, salt3, salt4, salt5):
        value = salt2
        units, second_last, hundreds = value % 10, (value // 10) % 10, (value // 100) % 10
        index = units + second_last + hundreds
        return self.MEMORY[index * 4 // 4] + 22

    def rdx(self, salt1, salt2, salt3, salt4, salt5):
        value = salt2
        units, second_last, hundreds = value % 10, (value // 10) % 10, (value // 100) % 10
        index = units + second_last + hundreds
        return self.MEMORY[index * 4 // 4] + 32

    def bdx(self, salt1, salt2, salt3, salt4, salt5):
        value = salt2
        units, second_last, hundreds = value % 10, (value // 10) % 10, (value // 100) % 10
        index = units + second_last + hundreds
        return self.MEMORY[index * 4 // 4] + 60

    def ndx(self, salt1, salt2, salt3, salt4, salt5):
        value = salt2
        units, second_last, hundreds = value % 10, (value // 10) % 10, (value // 100) % 10
        index = units + second_last + hundreds
        return self.MEMORY[index * 4 // 4] + 88

    def mdx(self, salt1, salt2, salt3, salt4, salt5):
        value = salt2
        units, second_last, hundreds = value % 10, (value // 10) % 10, (value // 100) % 10
        index = units + second_last + hundreds
        return self.MEMORY[index * 4 // 4] + 110

    def parse_token_response(self, token_response):
        n = self.cdx(token_response['salt1'], token_response['salt2'], token_response['salt3'], token_response['salt4'], token_response['salt5'])
        l = self.rdx(token_response['salt1'], token_response['salt2'], token_response['salt4'], token_response['salt3'], token_response['salt5'])
        o = self.bdx(token_response['salt1'], token_response['salt2'], token_response['salt4'], token_response['salt3'], token_response['salt5'])
        p = self.ndx(token_response['salt1'], token_response['salt2'], token_response['salt4'], token_response['salt3'], token_response['salt5'])
        q = self.mdx(token_response['salt1'], token_response['salt2'], token_response['salt4'], token_response['salt3'], token_response['salt5'])
        i = self.cdx(token_response['salt2'], token_response['salt1'], token_response['salt3'], token_response['salt5'], token_response['salt4'])
        r = self.rdx(token_response['salt2'], token_response['salt1'], token_response['salt3'], token_response['salt4'], token_response['salt5'])
        s = self.bdx(token_response['salt2'], token_response['salt1'], token_response['salt4'], token_response['salt3'], token_response['salt5'])
        t = self.ndx(token_response['salt2'], token_response['salt1'], token_response['salt4'], token_response['salt3'], token_response['salt5'])
        u = self.mdx(token_response['salt2'], token_response['salt1'], token_response['salt4'], token_response['salt3'], token_response['salt5'])

        access_token = token_response['accessToken']
        refresh_token = token_response['refreshToken']
        parsed_access_token = (access_token[0:n] + access_token[n+1:l] + access_token[l+1:o] + access_token[o+1:p] + access_token[p+1:q] + access_token[q+1:])
        parsed_refresh_token = (refresh_token[0:i] + refresh_token[i+1:r] + refresh_token[r+1:s] + refresh_token[s+1:t] + refresh_token[t+1:u] + refresh_token[u+1:])
        return parsed_access_token, parsed_refresh_token, token_response

class TokenCache:
    def __init__(self, ttl=300):  # 5-minute TTL
        self.token = None
        self.token_response = None
        self.expiry = 0
        self.ttl = ttl

    def is_valid(self):
        return self.token and time.time() < self.expiry

    def set_token(self, token, token_response):
        self.token = token
        self.token_response = token_response
        self.expiry = time.time() + self.ttl

    def get_token(self):
        return self.token, self.token_response

class PayloadParser:
    def __init__(self):
        self.dummyData = [147, 117, 239, 143, 157, 312, 161, 612, 512, 804, 411, 527, 170, 511, 421, 667, 764, 621, 301, 106, 133, 793, 411, 511, 312, 423, 344, 346, 653, 758, 342, 222, 236, 811, 711, 611, 122, 447, 128, 199, 183, 135, 489, 703, 800, 745, 152, 863, 134, 211, 142, 564, 375, 793, 212, 153, 138, 153, 648, 611, 151, 649, 318, 143, 117, 756, 119, 141, 717, 113, 112, 146, 162, 660, 693, 261, 362, 354, 251, 641, 157, 178, 631, 192, 734, 445, 192, 883, 187, 122, 591, 731, 852, 384, 565, 596, 451, 772, 624, 691]
        self.url = f"{ROOT_URL}{api_dict['marketopen_api']['api']}"
        self.method = api_dict['marketopen_api']['method']
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
        self.id_cache = {}  # Cache ID by date

    async def return_payload(self, access_token_value, which=None, session=None):
        today = datetime.now().day
        cache_key = (today, which)
        if cache_key in self.id_cache:
            return self.id_cache[cache_key]

        headers = {'Authorization': f'Salter {access_token_value[0]}', **self.headers}
        async with session.request(self.method, self.url, headers=headers, json={}) as response:
            response.raise_for_status()
            content = await response.json()
            given_id = content["id"]
            payload_id = self.dummyData[given_id] + given_id + 2 * today

        if which == 'stock-live':
            self.id_cache[cache_key] = payload_id
            return payload_id

        index_value = 3 if payload_id % 10 < 5 else 1
        payload_id = payload_id + access_token_value[1].get(f"salt{index_value+1}") * today - access_token_value[1].get(f"salt{index_value}")
        self.id_cache[cache_key] = payload_id
        return payload_id

class Nepse:
    def __init__(self):
        self.parser_obj = PayloadParser()
        self.token_parser = TokenParser()
        self.token_cache = TokenCache()
        self.token_url = ROOT_URL + api_dict['authenticate_api']['api']
        self.token_method = api_dict['authenticate_api']['method']
        self.headers = {
            'Host': 'www.nepalstock.com',
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.nepalstock.com/',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'TE': 'Trailers',
        }

    async def get_valid_token(self, session):
        if self.token_cache.is_valid():
            return self.token_cache.get_token()
        disable_warnings(InsecureRequestWarning)
        async with session.request(self.token_method, self.token_url, headers=self.headers, ssl=False) as response:
            response.raise_for_status()
            token_response = await response.json()
            for salt_index in range(1, 6):
                token_response[f'salt{salt_index}'] = int(token_response[f'salt{salt_index}'])
            access_token, refresh_token, token_response = self.token_parser.parse_token_response(token_response)
            self.token_cache.set_token((access_token, token_response), token_response)
            return access_token, token_response

    async def request_api(self, url, access_token, session, method='GET', which_payload=None, querystring=None, payload=None):
        headers = {'Authorization': f'Salter {access_token[0]}', **self.headers}
        if payload is None:
            payload = {'id': await self.parser_obj.return_payload(access_token, which=which_payload, session=session)}
        try:
            async with session.request(method, url, headers=headers, json=payload, params=querystring, ssl=False) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as exp:
            raise ValueError(f"Error sending request: {exp}")

class Nepse_scraper:
    SLEEP_TIME = 1000  # Reduced initial retry delay
    MAX_RETRIES = 3

    def __init__(self):
        self.nepse_obj = Nepse()
        self.desired_status = 200

    async def call_nepse_function(self, url, method, querystring=None, payload=None, which_payload=None):
        async with aiohttp.ClientSession() as session:
            for attempt in range(self.MAX_RETRIES):
                try:
                    access_token = await self.nepse_obj.get_valid_token(session)
                    response = await self.nepse_obj.request_api(
                        url, access_token=access_token, session=session, method=method,
                        querystring=querystring, payload=payload, which_payload=which_payload)
                    return response
                except ValueError as exp:
                    if attempt == self.MAX_RETRIES - 1:
                        raise ValueError(f'Unexpected Error after {self.MAX_RETRIES} attempts: {exp}')
                    await asyncio.sleep(self.SLEEP_TIME / 1000 * (2 ** attempt))  # Exponential backoff
                except aiohttp.ClientResponseError as exp:
                    if exp.status != self.desired_status:
                        raise ValueError(f'Unexpected status code: {exp.status}')
                    raise

    async def get_head_indices(self):
        api = ROOT_URL + api_dict['head_indices_api']['api']
        method = api_dict['head_indices_api']['method']
        querystring = {"page": "0", "size": "500"}
        sector_index = await self._get_sector_index()
        tasks = [self.call_nepse_function(url=f"{api}/{val['id']}", method=method, querystring=querystring) for val in sector_index]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {val['id']: result for val, result in zip(sector_index, results) if not isinstance(result, Exception)}

    async def get_ticker_info(self, ticker=None):
        if not ticker:
            raise ValueError('Ticker is required')
        if isinstance(ticker, str):
            ticker = [ticker]
        ticker = [x.upper() for x in ticker]
        values = await self._return_ticker_id(ticker)
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.nepse_obj.request_api(
                    url=f"{ROOT_URL}{api_dict['ticker_info_api']['api']}/{value}",
                    access_token=await self.nepse_obj.get_valid_token(session),
                    session=session, method=api_dict['ticker_info_api']['method'], which_payload='stock-live'
                ) for key, value in values.items()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return_value = {key: result for key, result in zip(values.keys(), results) if not isinstance(result, Exception)}
            return return_value[ticker[0]] if len(ticker) == 1 else return_value

    async def _get_security(self):
        api = ROOT_URL + api_dict['security']['api']
        method = api_dict['security']['method']
        return await self.call_nepse_function(url=api, method=method)

    async def _get_sector_index(self):
        api = ROOT_URL + api_dict['sector_index_api']['api']
        method = api_dict['sector_index_api']['method']
        querystring = {"page": "0", "size": "500"}
        return await self.call_nepse_function(url=api, method=method, querystring=querystring)

    async def _return_ticker_id(self, ticker_list):
        all_security = await self._get_security()
        values = {d.get('symbol'): d.get('id') for d in all_security if d.get('symbol') in ticker_list}
        if len(ticker_list) != len(values.keys()):
            raise ValueError(f"{set(ticker_list).difference(values.keys())}: Not Found")
        return values

    async def is_trading_day(self):
        api = ROOT_URL + api_dict['marketopen_api']['api']
        method = api_dict['marketopen_api']['method']
        response = await self.call_nepse_function(url=api, method=method)
        date_ = response['asOf'].split('T')[0]
        return date_ == str(date.today())
    
#     # Other methods can be similarly updated to use async/await and the client session
# class Nepse_scraper:
    # SLEEP_TIME = 3000

    # def __init__(self):
    #     self.nepse_obj = Nepse()
    #     self.desired_status = 200

    # @retry(wait_fixed=SLEEP_TIME)
    # def call_nepse_function(self, url, method, querystring=None, payload=None, which_payload=None):
    #     try:
    #         access_token = self.nepse_obj.get_valid_token()
    #         response = self.nepse_obj.return_data(
    #             url, access_token=access_token, method=method, querystring=querystring, payload=payload, which_payload=which_payload)
    #         if response.status_code != self.desired_status:
    #             raise ValueError(f'Unexpected status code: {response.status_code}')
    #         return response.json()
    #     except Exception as exp:
    #         raise ValueError(f'Unexpected Error: {exp}')

    # def _get_security(self):
    #     api = ROOT_URL + api_dict['security']['api']
    #     method = api_dict['security']['method']
    #     return self.call_nepse_function(url=api, method=method)

    # def is_trading_day(self):
    #     api = ROOT_URL + api_dict['marketopen_api']['api']
    #     method = api_dict['marketopen_api']['method']
    #     response = self.call_nepse_function(url=api, method=method)
    #     date_ = response['asOf'].split('T')[0]
    #     return date_ == str(date.today())

    # def is_market_open(self):
    #     api = ROOT_URL + api_dict['marketopen_api']['api']
    #     method = api_dict['marketopen_api']['method']
    #     response = self.call_nepse_function(url=api, method=method)
    #     return response['isOpen'] == 'OPEN'

    # def get_today_price(self, date_=None):
    #     api = ROOT_URL + api_dict['today_price_api']['api']
    #     method = api_dict['today_price_api']['method']
    #     querystring = {"page": "0", "size": "500", "businessDate": date_}
    #     return self.call_nepse_function(url=api, method=method, querystring=querystring)

    # def get_head_indices(self):
    #     api = ROOT_URL + api_dict['head_indices_api']['api']
    #     method = api_dict['head_indices_api']['method']
    #     querystring = {"page": "0", "size": "500"}
    #     dicts = {}
    #     sector_index = self._get_sector_index()
    #     for val in sector_index:
    #         dicts[val['id']] = self.call_nepse_function(
    #             url=api + '/' + str(val['id']), method=method, querystring=querystring)
    #     return dicts

    # def get_sectorwise_summary(self, date_=None):
    #     api = ROOT_URL + api_dict['sectorwise_summary_api']['api']
    #     method = api_dict['sectorwise_summary_api']['method']
    #     querystring = {"page": "0", "size": "500", "businessDate": date_}
    #     return self.call_nepse_function(url=api, method=method, querystring=querystring)

    # def get_market_summary(self, date_=None):
    #     api = ROOT_URL + api_dict['market_summary_history_api']['api']
    #     method = api_dict['market_summary_history_api']['method']
    #     querystring = {"page": "0", "size": "500", "businessDate": date_}
    #     return self.call_nepse_function(url=api, method=method, querystring=querystring)

    # def get_news(self):
    #     api = ROOT_URL + api_dict['disclosure']['api']
    #     method = api_dict['disclosure']['method']
    #     return self.call_nepse_function(url=api, method=method)

    # def get_top_gainer(self):
    #     api = ROOT_URL + api_dict['top_gainer']['api']
    #     method = api_dict['top_gainer']['method']
    #     return self.call_nepse_function(url=api, method=method)

    # def get_top_loser(self):
    #     api = ROOT_URL + api_dict['top_loser']['api']
    #     method = api_dict['top_loser']['method']
    #     return self.call_nepse_function(url=api, method=method)

    # def get_top_turnover(self):
    #     api = ROOT_URL + api_dict['top_turnover']['api']
    #     method = api_dict['top_turnover']['method']
    #     return self.call_nepse_function(url=api, method=method)

    # def get_top_trade(self):
    #     api = ROOT_URL + api_dict['top_trade']['api']
    #     method = api_dict['top_trade']['method']
    #     return self.call_nepse_function(url=api, method=method)

    # def get_top_transaction(self):
    #     api = ROOT_URL + api_dict['top_transaction']['api']
    #     method = api_dict['top_transaction']['method']
    #     return self.call_nepse_function(url=api, method=method)

    # def get_today_market_summary(self):
    #     api = ROOT_URL + api_dict['market_summary_api']['api']
    #     method = api_dict['market_summary_api']['method']
    #     return self.call_nepse_function(url=api, method=method)

    # def get_all_security(self):
    #     api = ROOT_URL + api_dict['security_api']['api']
    #     method = api_dict['security_api']['method']
    #     return self.call_nepse_function(url=api, method=method)

    # def get_marketcap(self):
    #     api = ROOT_URL + api_dict['marketcap_api']['api']
    #     method = api_dict['marketcap_api']['method']
    #     return self.call_nepse_function(url=api, method=method)

    # def get_trading_average(self, date_=None, n_days=120):
    #     if n_days < 1 or n_days > 180:
    #         raise ValueError("n_days must be between 1 and 180")
    #     api = ROOT_URL + api_dict['trading_average_api']['api']
    #     method = api_dict['trading_average_api']['method']
    #     querystring = {"page": "0", "size": "500", "businessDate": date_, "nDays": n_days}
    #     return self.call_nepse_function(url=api, method=method, querystring=querystring)

    # def get_broker(self, member_name="", contact_person="", contact_number="", member_code="", province_id=0, district_id=0, municipality_id=0):
    #     api = ROOT_URL + api_dict['broker_api']['api']
    #     method = api_dict['broker_api']['method']
    #     querystring = {"page": "0", "size": "500"}
    #     payload = {
    #         "memberName": member_name,
    #         "contactPerson": contact_person,
    #         "contactNumber": contact_number,
    #         "memberCode": member_code,
    #         "provinceId": province_id,
    #         "districtId": district_id,
    #         "municipalityId": municipality_id
    #     }
    #     return self.call_nepse_function(url=api, method=method, querystring=querystring, payload=payload)

    # def get_sector_detail(self):
    #     api = ROOT_URL + api_dict['sector_api']['api']
    #     method = api_dict['sector_api']['method']
    #     querystring = {"page": "0", "size": "500"}
    #     return self.call_nepse_function(url=api, method=method, querystring=querystring)

    # def _get_sector_index(self):
    #     api = ROOT_URL + api_dict['sector_index_api']['api']
    #     method = api_dict['sector_index_api']['method']
    #     querystring = {"page": "0", "size": "500"}
    #     return self.call_nepse_function(url=api, method=method, querystring=querystring)

    # def _return_ticker_id(self, ticker_list):
    #     all_security = self._get_security()
    #     values = {d.get('symbol'): d.get('id') for d in all_security if d.get('symbol') in ticker_list}
    #     if len(ticker_list) != len(values.keys()):
    #         raise ValueError(f"{set(ticker_list).difference(values.keys())}: Not Found")
    #     return values

    # def get_ticker_info(self, ticker=None):
    #     if not ticker:
    #         raise ValueError('Ticker is required')
    #     if isinstance(ticker, str):
    #         ticker = [ticker]
    #     ticker = [x.upper() for x in ticker]
    #     values = self._return_ticker_id(ticker)
    #     return_value = {}
    #     for key, value in values.items():
    #         api = ROOT_URL + api_dict['ticker_info_api']['api'] + '/' + str(value)
    #         method = api_dict['ticker_info_api']['method']
    #         return_value[key] = self.call_nepse_function(url=api, method=method, which_payload='stock-live')
    #     return return_value[ticker[0]] if len(ticker) == 1 else return_value

    # def get_ticker_contact_info(self, ticker=None):
    #     if not ticker:
    #         raise ValueError('Ticker is required')
    #     if isinstance(ticker, str):
    #         ticker = [ticker]
    #     ticker = [x.upper() for x in ticker]
    #     values = self._return_ticker_id(ticker)
    #     return_value = {}
    #     for key, value in values.items():
    #         api = ROOT_URL + api_dict['ticker_contact_api']['api'] + '/' + str(value)
    #         method = api_dict['ticker_contact_api']['method']
    #         return_value[key] = self.call_nepse_function(url=api, method=method)
    #     return return_value[ticker[0]] if len(ticker) == 1 else return_value

    # def get_live_indices(self, indices_id=58):
    #     if indices_id < 51 or indices_id > 67:
    #         raise ValueError(f"'{indices_id}' is not valid indices ID.")
    #     api = ROOT_URL + api_dict['indices_live_api']['api'] + "/" + str(indices_id)
    #     method = api_dict['indices_live_api']['method']
    #     return self.call_nepse_function(url=api, method=method, which_payload='sector-live')

    # def get_ticker_price(self, ticker=None):
    #     if not ticker:
    #         raise ValueError('Ticker is required')
    #     if isinstance(ticker, str):
    #         ticker = [ticker]
    #     ticker = [x.upper() for x in ticker]
    #     values = self._return_ticker_id(ticker)
    #     return_value = {}
    #     for key, value in values.items():
    #         api = ROOT_URL + api_dict['ticker_price_api']['api'] + '/' + str(value)
    #         method = api_dict['ticker_price_api']['method']
    #         return_value[key] = self.call_nepse_function(url=api, method=method)
    #     return return_value[ticker[0]] if len(ticker) == 1 else return_value

    # def get_live_stock(self):
    #     if not self.is_market_open():
    #         raise ValueError('Market is closed')
    #     api = ROOT_URL + api_dict['stock_live_api']['api']
    #     method = api_dict['stock_live_api']['method']
    #     return self.call_nepse_function(url=api, method=method, which_payload='stock-live')