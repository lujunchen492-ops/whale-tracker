import requests
import time
import sqlite3
import os
import sys
from datetime import datetime
from requests.exceptions import RequestException
from http.client import IncompleteRead
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 全局运行状态
is_running = True

# --- 配置部分 ---
API_KEY = os.getenv("ETHERSCAN_API_KEY")
BASE_URL = "https://api.etherscan.io/v2/api"
DB_NAME = os.getenv("DB_NAME", "whale_data.db")

# 1. 巨鲸监控列表 (WATCH_LIST)
WATCH_LIST = {
    "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B": "V神 (Vitalik)",
    "0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE": "币安钱包",
    "0x28C6c06290CC3F9517c3972ad218315B227a7011": "Jump Trading",
}

# 2. 代币合约配置 (ERC-20 Tokens)
TOKENS = {
    "USDT": {
        "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "decimals": 6,
        "threshold": int(os.getenv("USDT_THRESHOLD", 1000000)), # 100万 USDT
        "color": "\033[92m"   # 绿色
    },
    "USDC": {
        "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "decimals": 6,
        "threshold": int(os.getenv("USDC_THRESHOLD", 1000000)), # 100万 USDC
        "color": "\033[96m"   # 青色
    },
    "WBTC": {
        "address": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "decimals": 8,
        "threshold": int(os.getenv("WBTC_THRESHOLD", 50)),      # 50 WBTC
        "color": "\033[93m"   # 黄色
    }
}

# 原生 ETH 配置
ETH_CONFIG = {
    "threshold": int(os.getenv("ETH_THRESHOLD", 1000)),        # 1000 ETH
    "color": "\033[95m"       # 紫色
}

# ANSI 颜色
YELLOW = "\033[93m"
RESET = "\033[0m"
RED = "\033[91m"
CYAN = "\033[96m"

# --- 数据库操作 ---

# 全局数据库连接变量
_db_conn = None

def get_db_conn():
    """获取单例数据库连接"""
    global _db_conn
    if _db_conn is None:
        _db_conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return _db_conn

def close_db_conn():
    """关闭数据库连接"""
    global _db_conn
    if _db_conn:
        _db_conn.close()
        _db_conn = None

def init_db():
    """初始化数据库和表结构"""
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                block_number INTEGER,
                tx_hash TEXT UNIQUE,
                from_address TEXT,
                to_address TEXT,
                value_eth REAL,
                token_symbol TEXT
            )
        ''')
        conn.commit()
        
        # 查询当前记录总数
        cursor.execute("SELECT COUNT(*) FROM transactions")
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        print(f"{RED}数据库初始化失败: {e}{RESET}")
        return 0

def save_transaction(timestamp, block_number, tx_hash, from_addr, to_addr, value, symbol):
    """将交易记录存入数据库"""
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO transactions 
            (timestamp, block_number, tx_hash, from_address, to_address, value_eth, token_symbol)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, block_number, tx_hash, from_addr, to_addr, value, symbol))
        conn.commit()
    except Exception as e:
        print(f"{YELLOW}警告：数据库写入失败: {e}{RESET}")

# --- 工具函数 ---

def safe_hex_to_int(hex_str):
    if not hex_str or not isinstance(hex_str, str):
        return 0
    try:
        return int(hex_str, 16)
    except ValueError:
        return 0

def make_request_with_retry(params, max_retries=3, retry_delay=2):
    for i in range(max_retries):
        try:
            response = requests.get(BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except (RequestException, IncompleteRead) as e:
            if i < max_retries - 1:
                print(f"{YELLOW}网络波动，正在重试... ({i+1}/{max_retries}){RESET}")
                time.sleep(retry_delay)
            else:
                return None
    return None

def get_latest_block_number():
    params = {"chainid": 1, "module": "proxy", "action": "eth_blockNumber", "apikey": API_KEY}
    data = make_request_with_retry(params)
    if data and "result" in data:
        return safe_hex_to_int(data["result"])
    return None

def get_block_by_number(block_number):
    params = {
        "chainid": 1, "module": "proxy", "action": "eth_getBlockByNumber",
        "tag": hex(block_number), "boolean": "true", "apikey": API_KEY
    }
    data = make_request_with_retry(params)
    if data and data.get("status") != "0":
        return data.get("result")
    return None

def parse_erc20_transfer(input_data):
    """解析 ERC-20 transfer 方法的 input 数据"""
    if not input_data or len(input_data) < 138 or not input_data.startswith("0xa9059cbb"):
        return None, None
    to_addr = "0x" + input_data[34:74]
    value = int(input_data[74:138], 16)
    return to_addr, value

# --- 主逻辑 ---

def monitor_whale_v4():
    global is_running
    # 初始化数据库并获取当前计数
    current_count = init_db()
    
    print("=" * 60)
    print("以太坊全链巨鲸监控系统 V4 (SQLite 持久化版)")
    print(f"监控代币: ETH, {', '.join(TOKENS.keys())}")
    print(f"{CYAN}当前数据库已记录 {current_count} 条巨鲸交易。{RESET}")
    print(f"{YELLOW}提示：按 Ctrl + C 可优雅退出程序。{RESET}")
    print("=" * 60)

    last_block = None
    watch_lower = {k.lower(): v for k, v in WATCH_LIST.items()}
    token_contracts = {v["address"].lower(): k for k, v in TOKENS.items()}

    try:
        while is_running:
            try:
                current_block = get_latest_block_number()
                if current_block and current_block != last_block:
                    if last_block is None:
                        last_block = current_block
                        print(f"初始化成功！当前区块: {current_block}")
                        continue

                    for block_num in range(last_block + 1, current_block + 1):
                        # 检查是否在处理区块中途收到了停止信号
                        if not is_running:
                            break

                        block_data = get_block_by_number(block_num)
                        if not block_data or "transactions" not in block_data:
                            print(f"{YELLOW}跳过区块 {block_num}{RESET}")
                            continue

                        transactions = block_data["transactions"]
                        now = datetime.now()
                        time_str = now.strftime("%H:%M:%S")
                        timestamp_full = now.strftime("%Y-%m-%d %H:%M:%S")
                        
                        for tx in transactions:
                            from_addr = (tx.get("from") or "").lower()
                            to_addr = (tx.get("to") or "").lower()
                            input_data = tx.get("input", "")
                            
                            symbol = "ETH"
                            amount = safe_hex_to_int(tx.get("value")) / 1e18
                            is_whale_tx = False
                            direction = "TRANSFER"

                            # 1. 检查是否是 ERC-20 转账
                            if to_addr in token_contracts:
                                token_symbol = token_contracts[to_addr]
                                t_to, t_val = parse_erc20_transfer(input_data)
                                if t_to:
                                    symbol = token_symbol
                                    config = TOKENS[symbol]
                                    amount = t_val / (10 ** config["decimals"])
                                    to_addr = t_to.lower()
                                    if amount >= config["threshold"]:
                                        is_whale_tx = True

                            # 2. 检查原生 ETH 大额
                            elif amount >= ETH_CONFIG["threshold"]:
                                is_whale_tx = True

                            # 3. 检查是否涉及 WATCH_LIST
                            is_watched = False
                            watch_name = ""
                            if from_addr in watch_lower:
                                is_watched = True
                                watch_name = f"来自 {watch_lower[from_addr]}"
                                direction = "OUT"
                            elif to_addr in watch_lower:
                                is_watched = True
                                watch_name = f"发往 {watch_lower[to_addr]}"
                                direction = "IN"

                            # 4. 打印并保存逻辑
                            if is_whale_tx or is_watched:
                                # 保存到数据库
                                save_transaction(
                                    timestamp_full, block_num, tx['hash'], 
                                    from_addr, to_addr, amount, symbol
                                )

                                color = TOKENS[symbol]["color"] if symbol in TOKENS else ETH_CONFIG["color"]
                                label = f"[{symbol}]"
                                
                                # 终端输出
                                output = f"{time_str} | {color}{label:6}{RESET} | {amount:12,.2f} | {direction:8} | {tx['hash']}"
                                if is_watched:
                                    output += f" | {RED}重点关注: {watch_name}{RESET}"
                                print(output)

                    last_block = current_block
            except Exception as e:
                if is_running: # 只有在非停机状态下才打印异常
                    print(f"监控异常: {e}")
            
            # 在等待下一次请求前再次检查状态
            if is_running:
                time.sleep(15)

    except KeyboardInterrupt:
        is_running = False
        print(f"\n{YELLOW}⚠️ 检测到退出信号，正在执行优雅停机...{RESET}")
    finally:
        close_db_conn()
        print(f"{CYAN}✅ 数据库连接已安全关闭，程序退出。{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    if not API_KEY:
        print(f"{RED}错误：未在 .env 中找到 ETHERSCAN_API_KEY。{RESET}")
    else:
        monitor_whale_v4()
