import requests
import time
from requests.exceptions import RequestException
from http.client import IncompleteRead
from src.config import Config

class EtherscanClient:
    """Etherscan API 请求封装类"""
    def __init__(self, api_key=Config.API_KEY):
        self.api_key = api_key
        self.base_url = Config.BASE_URL

    def _make_request(self, params, max_retries=3, retry_delay=2):
        """通用的重试请求逻辑"""
        params["apikey"] = self.api_key
        for i in range(max_retries):
            try:
                response = requests.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()
                return response.json()
            except (RequestException, IncompleteRead) as e:
                if i < max_retries - 1:
                    print(f"{Config.YELLOW}网络波动，正在重试... ({i+1}/{max_retries}){Config.RESET}")
                    time.sleep(retry_delay)
                else:
                    return None
        return None

    def get_latest_block_number(self):
        """获取最新区块号"""
        params = {"chainid": 1, "module": "proxy", "action": "eth_blockNumber"}
        data = self._make_request(params)
        if data and "result" in data:
            try:
                return int(data["result"], 16)
            except ValueError:
                return None
        return None

    def get_block_by_number(self, block_number):
        """获取区块详细信息"""
        params = {
            "chainid": 1, "module": "proxy", "action": "eth_getBlockByNumber",
            "tag": hex(block_number), "boolean": "true"
        }
        data = self._make_request(params)
        if data and data.get("status") != "0":
            return data.get("result")
        return None

    @staticmethod
    def parse_erc20_transfer(input_data):
        """静态方法：解析 ERC-20 转账数据"""
        if not input_data or len(input_data) < 138 or not input_data.startswith("0xa9059cbb"):
            return None, None
        to_addr = "0x" + input_data[34:74]
        try:
            value = int(input_data[74:138], 16)
            return to_addr, value
        except ValueError:
            return None, None
