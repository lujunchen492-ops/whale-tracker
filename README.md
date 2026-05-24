# 🐋 Ethereum Whale Tracker (以太坊全链巨鲸监控系统)

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

## 📖 项目简介
本项目是一款基于 Python 开发的高性能、生产级以太坊全链大额交易（巨鲸）实时监控与数据持久化系统。系统能够自动扫描以太坊全链最新区块，识别原生 ETH 及主流 ERC-20 代币（USDT, USDC, WBTC）的大额异动，并对重点关注地址进行精准追踪。

## 🛠️ 核心技术栈
- **语言框架**: Python 3.8+
- **链上接口**: Etherscan API V2 (Proxy Module)
- **存储引擎**: SQLite (Structured Persistence)
- **环境管理**: Python-dotenv (Environment Variable Isolation)
- **信号处理**: Signal / Sys (Graceful Shutdown Control)

## 🌟 项目核心亮点

### 1. API 协议深度适配
完美适配 2026 年最新的 **Etherscan API V2** 标准。系统内置了针对链上高精度十六进制（Hexadecimal）数据的安全转换引擎，能够精准处理 `Value`、`GasPrice` 等字段，确保大额交易金额转换零误差。

### 2. 高可用容错机制 (High Availability)
针对跨境网络环境的复杂性，设计并实现了基于**异常捕获与指数退避（Exponential Backoff）**的重试机制。系统能自动识别 `IncompleteRead`、`Timeout` 等网络抖动，确保在极端的网络条件下仍能实现 7x24 小时不间断运行。

### 3. 结构化数据持久化 (Persistence)
采用轻量级、高性能的 **SQLite** 数据库作为存储后端。设计了高度优化的事务写入逻辑，实现大额交易数据的秒级落盘。这为后续的链上行为分析、资产审计及历史回溯提供了坚实的数据基础。

### 4. 优雅停机 (Graceful Shutdown)
通过捕获 `SIGINT` (Ctrl+C) 信号，系统实现了工业级的优雅退出流程。在进程退出前，系统会安全阻塞当前正在处理的任务流，确保当前区块的数据事务完整提交，并强制刷新缓冲区释放数据库连接，从根源上杜绝了数据库损坏与数据丢失风险。

## 📂 项目文件结构
```text
whale_tracker/
├── src/                    # 核心源代码目录
│   ├── __init__.py         # 模块化标识
│   ├── config.py           # 配置管理 (Class: Config)
│   ├── database.py         # 数据持久化封装 (Class: WhaleDatabase)
│   ├── client.py           # API 请求客户端 (Class: EtherscanClient)
│   └── tracker.py          # 核心业务逻辑 (Class: WhaleTracker)
├── main.py                 # 程序唯一入口，生命周期管理
├── .env                    # 敏感环境变量 (已通过 .gitignore 排除)
├── .env.example            # 环境变量配置模板
├── .gitignore              # Git 忽略规则
├── requirements.txt        # 项目依赖清单
└── README.md               # 项目技术说明文档
```

## 📋 数据库设计描述
系统自动维护 `transactions` 表，其核心字段设计如下：

| 字段名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `id` | INTEGER | 主键，自增唯一标识 |
| `timestamp` | TEXT | 交易发生的日期时间（北京时间） |
| `block_number` | INTEGER | 交易所属的区块高度 |
| `tx_hash` | TEXT | 交易哈希 (Unique，防止重复记录) |
| `from_address` | TEXT | 发送方钱包地址 |
| `to_address` | TEXT | 接收方钱包地址 |
| `value_eth` | REAL | 交易金额（已换算为对应代币单位） |
| `token_symbol` | TEXT | 代币符号（ETH, USDT, USDC, WBTC） |

## 🚀 环境配置与运行指南

### 1. 获取 API Key
访问 [Etherscan](https://etherscan.io/apis) 注册并获取你的 API Key。

### 2. 自定义监控名单 (watch_list.txt)
在项目根目录下，你可以通过 `watch_list.txt` 文件灵活管理监控名单。系统会自动识别并追踪这些地址的每一笔动向。
- **格式要求**：`钱包地址 # 备注名称`（每行一个）。
- **示例内容**：
  ```text
  0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B # V神 (Vitalik)
  0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE # 币安热钱包
  ```
- **核心逻辑**：系统在启动时会自动加载该文件，过滤掉注释和空行，并对匹配到的地址触发 `【目标触发】` 特别提醒。

### 3. 配置环境变量
在项目根目录创建 `.env` 文件，内容如下：
```env
ETHERSCAN_API_KEY=你的_API_KEY_在此
DB_NAME=whale_data.db
ETH_THRESHOLD=1000
USDT_THRESHOLD=1000000
USDC_THRESHOLD=1000000
WBTC_THRESHOLD=50
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 启动项目
```bash
python main.py
```

---
*本项目仅供技术交流与学习使用，投资有风险，监控数据仅供参考。*
