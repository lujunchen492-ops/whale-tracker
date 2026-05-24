import time
from datetime import datetime
from src.config import Config
from src.database import WhaleDatabase
from src.client import EtherscanClient

class WhaleTracker:
    """巨鲸监控主逻辑类"""
    def __init__(self):
        self.db = WhaleDatabase()
        self.client = EtherscanClient()
        self.is_running = True
        self.last_block = None
        
        # 动态加载外部监控名单
        self.watch_list = Config.load_watch_list()
        self.token_contracts = {v["address"].lower(): k for k, v in Config.TOKENS.items()}

    def stop(self):
        """停止监控"""
        self.is_running = False

    def run(self):
        """主运行循环"""
        current_count = self.db.get_record_count()
        self._print_welcome(current_count)

        while self.is_running:
            try:
                # 每次获取最新区块前，也可以选择性重新加载名单（可选，目前实现为启动加载）
                # self.watch_list = Config.load_watch_list() 
                current_block = self.client.get_latest_block_number()
                if current_block and current_block != self.last_block:
                    if self.last_block is None:
                        self.last_block = current_block
                        print(f"初始化成功！当前区块: {current_block}")
                        continue

                    for block_num in range(self.last_block + 1, current_block + 1):
                        if not self.is_running: break
                        self._process_block(block_num)

                    self.last_block = current_block
            except Exception as e:
                if self.is_running:
                    print(f"监控异常: {e}")
            
            if self.is_running:
                time.sleep(15)
        
        self.db.close()

    def _process_block(self, block_num):
        """处理单个区块"""
        block_data = self.client.get_block_by_number(block_num)
        if not block_data or "transactions" not in block_data:
            print(f"{Config.YELLOW}跳过区块 {block_num}{Config.RESET}")
            return

        transactions = block_data["transactions"]
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        timestamp_full = now.strftime("%Y-%m-%d %H:%M:%S")

        for tx in transactions:
            self._analyze_transaction(tx, block_num, time_str, timestamp_full)

    def _analyze_transaction(self, tx, block_num, time_str, timestamp_full):
        """分析单笔交易"""
        from_addr = (tx.get("from") or "").lower()
        to_addr = (tx.get("to") or "").lower()
        input_data = tx.get("input", "")
        
        symbol = "ETH"
        try:
            amount = int(tx.get("value", "0"), 16) / 1e18
        except ValueError:
            amount = 0
            
        is_whale_tx = False
        direction = "TRANSFER"

        # 1. 检查 ERC-20
        if to_addr in self.token_contracts:
            token_symbol = self.token_contracts[to_addr]
            t_to, t_val = self.client.parse_erc20_transfer(input_data)
            if t_to:
                symbol = token_symbol
                config = Config.TOKENS[symbol]
                amount = t_val / (10 ** config["decimals"])
                to_addr = t_to.lower()
                if amount >= config["threshold"]:
                    is_whale_tx = True

        # 2. 检查 ETH
        elif amount >= Config.ETH_CONFIG["threshold"]:
            is_whale_tx = True

        # 3. 检查监控列表
        is_watched = False
        watch_name = ""
        if from_addr in self.watch_list:
            is_watched = True
            watch_name = f"来自 {self.watch_list[from_addr]}"
            direction = "OUT"
        elif to_addr in self.watch_list:
            is_watched = True
            watch_name = f"发往 {self.watch_list[to_addr]}"
            direction = "IN"

        # 4. 打印与保存
        if is_whale_tx or is_watched:
            self.db.save_transaction(
                timestamp_full, block_num, tx['hash'], 
                from_addr, to_addr, amount, symbol
            )
            # 如果是重点关注地址，输出时增加前缀
            display_name = watch_name
            if is_watched:
                display_name = f"【目标触发】{watch_name}"
            
            self._print_output(time_str, symbol, amount, direction, tx['hash'], is_watched, display_name)

    def _print_welcome(self, count):
        print("=" * 60)
        print("以太坊全链巨鲸监控系统 V5 (模块化重构版)")
        print(f"监控代币: ETH, {', '.join(Config.TOKENS.keys())}")
        print(f"{Config.CYAN}当前数据库已记录 {count} 条巨鲸交易。{Config.RESET}")
        print(f"{Config.YELLOW}提示：按 Ctrl + C 可优雅退出程序。{Config.RESET}")
        print("=" * 60)

    def _print_output(self, time_str, symbol, amount, direction, tx_hash, is_watched, watch_name):
        color = Config.TOKENS[symbol]["color"] if symbol in Config.TOKENS else Config.ETH_CONFIG["color"]
        label = f"[{symbol}]"
        output = f"{time_str} | {color}{label:6}{Config.RESET} | {amount:12,.2f} | {direction:8} | {tx_hash}"
        if is_watched:
            output += f" | {Config.RED}重点关注: {watch_name}{Config.RESET}"
        print(output)
