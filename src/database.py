import sqlite3
from src.config import Config

class WhaleDatabase:
    """数据库操作封装类"""
    def __init__(self, db_name=Config.DB_NAME):
        self.db_name = db_name
        self.conn = None
        self._init_connection()

    def _init_connection(self):
        """初始化连接并创建表"""
        try:
            # 确保数据库路径正确，如果是相对路径，则相对于 main.py 运行位置
            self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
            cursor = self.conn.cursor()
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
            self.conn.commit()
        except Exception as e:
            # 打印更详细的错误信息
            import traceback
            print(f"{Config.RED}数据库初始化失败: {e}{Config.RESET}")
            traceback.print_exc()

    def get_record_count(self):
        """获取当前记录总数"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM transactions")
            return cursor.fetchone()[0]
        except Exception:
            return 0

    def save_transaction(self, timestamp, block_number, tx_hash, from_addr, to_addr, value, symbol):
        """保存交易记录"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO transactions 
                (timestamp, block_number, tx_hash, from_address, to_address, value_eth, token_symbol)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, block_number, tx_hash, from_addr, to_addr, value, symbol))
            self.conn.commit()
        except Exception as e:
            print(f"{Config.YELLOW}警告：数据库写入失败: {e}{Config.RESET}")

    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
