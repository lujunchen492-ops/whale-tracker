import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """配置管理类"""
    API_KEY = os.getenv("ETHERSCAN_API_KEY")
    BASE_URL = "https://api.etherscan.io/v2/api"
    
    # 使用绝对路径确保数据库在项目根目录
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_NAME = os.path.join(ROOT_DIR, os.getenv("DB_NAME", "whale_data.db"))
    WATCH_LIST_FILE = os.path.join(ROOT_DIR, "watch_list.txt")
    
    @classmethod
    def load_watch_list(cls):
        """从外部文本文件动态加载监控名单"""
        watch_list = {}
        if not os.path.exists(cls.WATCH_LIST_FILE):
            try:
                with open(cls.WATCH_LIST_FILE, "w", encoding="utf-8") as f:
                    f.write("# 以太坊监控名单 (格式: 地址 # 备注)\n")
                print(f"{cls.YELLOW}提示：已自动创建空的监控名单文件 {cls.WATCH_LIST_FILE}{cls.RESET}")
            except Exception as e:
                print(f"{cls.RED}创建监控名单文件失败: {e}{cls.RESET}")
            return watch_list

        try:
            with open(cls.WATCH_LIST_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
                    # 处理带注释的行，例如: 0x123... # 备注
                    parts = line.split("#", 1)
                    address = parts[0].strip()
                    comment = parts[1].strip() if len(parts) > 1 else "未知巨鲸"
                    
                    # 校验以太坊地址格式 (0x 开头，42 位)
                    if address.startswith("0x") and len(address) == 42:
                        watch_list[address.lower()] = comment
        except Exception as e:
            print(f"{cls.RED}读取监控名单文件失败: {e}{cls.RESET}")
            
        return watch_list
    
    # 代币配置
    TOKENS = {
        "USDT": {
            "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "decimals": 6,
            "threshold": int(os.getenv("USDT_THRESHOLD", 1000000)),
            "color": "\033[92m"
        },
        "USDC": {
            "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "decimals": 6,
            "threshold": int(os.getenv("USDC_THRESHOLD", 1000000)),
            "color": "\033[96m"
        },
        "WBTC": {
            "address": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
            "decimals": 8,
            "threshold": int(os.getenv("WBTC_THRESHOLD", 50)),
            "color": "\033[93m"
        }
    }
    
    ETH_CONFIG = {
        "threshold": int(os.getenv("ETH_THRESHOLD", 1000)),
        "color": "\033[95m"
    }

    # ANSI 颜色
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    RED = "\033[91m"
    CYAN = "\033[96m"
