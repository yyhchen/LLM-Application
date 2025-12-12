#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主脚本，用于串行执行三个新闻爬虫脚本，防止AI API请求限制
"""
import os
import time
import subprocess
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 获取当前脚本所在目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 脚本路径列表（使用相对路径）
SCRIPTS = [
    os.path.join(CURRENT_DIR, "ai_daily_briefing", "ai_daily_news.py"),
    os.path.join(CURRENT_DIR, "car_daily_briefing", "car_news_crawler.py"),
    os.path.join(CURRENT_DIR, "finance_daily_briefing", "financial_news_crawler.py")
]

# 执行间隔时间（秒）
INTERVAL = 60

def run_script(script_path):
    """
    执行单个脚本
    
    Args:
        script_path: 脚本路径
    
    Returns:
        执行结果状态码
    """
    logger.info(f"开始执行脚本：{script_path}")
    
    # 获取脚本名称，用于日志记录
    script_name = os.path.basename(script_path)
    
    try:
        # 执行脚本
        result = subprocess.run(
            ["python3", script_path],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        
        # 记录标准输出
        if result.stdout:
            logger.info(f"脚本 {script_name} 输出：{result.stdout[:200]}...")  # 只显示前200个字符
        
        # 记录标准错误
        if result.stderr:
            logger.error(f"脚本 {script_name} 错误：{result.stderr}")
        
        logger.info(f"脚本 {script_name} 执行成功，状态码：{result.returncode}")
        return result.returncode
    except subprocess.CalledProcessError as e:
        logger.error(f"脚本 {script_name} 执行失败，状态码：{e.returncode}")
        logger.error(f"错误输出：{e.stderr}")
        return e.returncode
    except Exception as e:
        logger.error(f"执行脚本 {script_name} 时发生未知错误：{e}")
        return -1

def main():
    """
    主函数，串行执行所有脚本
    """
    logger.info("="*50)
    logger.info(f"开始执行新闻爬虫任务，当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"共 {len(SCRIPTS)} 个脚本，执行间隔：{INTERVAL} 秒")
    logger.info("="*50)
    
    # 遍历执行所有脚本
    for i, script in enumerate(SCRIPTS, 1):
        logger.info(f"\n[{i}/{len(SCRIPTS)}] 准备执行：{script}")
        
        # 执行脚本
        status_code = run_script(script)
        
        # 检查是否是最后一个脚本，如果不是则添加间隔
        if i < len(SCRIPTS):
            logger.info(f"脚本执行完成，等待 {INTERVAL} 秒后执行下一个脚本...")
            time.sleep(INTERVAL)
        else:
            logger.info("所有脚本执行完成！")
    
    logger.info("="*50)
    logger.info(f"新闻爬虫任务执行完毕，当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*50)

if __name__ == "__main__":
    main()