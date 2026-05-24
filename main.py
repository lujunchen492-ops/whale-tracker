import sys
from src.config import Config
from src.tracker import WhaleTracker

def main():
    if not Config.API_KEY:
        print(f"{Config.RED}错误：未在 .env 中找到 ETHERSCAN_API_KEY。{Config.RESET}")
        sys.exit(1)

    tracker = WhaleTracker()
    
    try:
        tracker.run()
    except KeyboardInterrupt:
        print(f"\n{Config.YELLOW}⚠️ 检测到退出信号，正在执行优雅停机...{Config.RESET}")
        tracker.stop()
        # tracker.run() 中的循环会因为 is_running=False 而结束并关闭数据库
    finally:
        print(f"{Config.CYAN}✅ 程序已安全退出。{Config.RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()
