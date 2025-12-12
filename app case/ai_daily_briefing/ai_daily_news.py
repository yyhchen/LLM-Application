import requests
from bs4 import BeautifulSoup
import re
import json
import asyncio
import os
import logging
import random
from typing import List, Dict, Optional, Any
from crawl4ai import AsyncWebCrawler
from datetime import datetime, timedelta
from openai import OpenAI
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# 配置常量
BASE_URL = "https://www.aibase.com/zh/news"
API_BASE_URL = "https://api.longcat.chat/openai"
MODEL_NAME = "LongCat-Flash-Chat"
JS_WAIT_TIME = 5000  # 毫秒
CRAWLER_TIMEOUT = 30000  # 毫秒
DEFAULT_NEWS_COUNT = 30
API_KEY_ENV_VAR = "MEITUAN_API_KEY"

# 系统常量
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据目录结构
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

# 获取当前年份和月份
current_year = datetime.now().strftime("%Y")
current_month = datetime.now().strftime("%m")

# 按年份/月份划分的目录
JSON_DIR = os.path.join(DATA_DIR, "json", current_year, current_month)
TXT_DIR = os.path.join(DATA_DIR, "txt", current_year, current_month)

# 确保目录存在
os.makedirs(JSON_DIR, exist_ok=True)
os.makedirs(TXT_DIR, exist_ok=True)

# 预编译正则表达式
NEWS_ID_PATTERN = re.compile(r'/news/(\d+)')
TITLE_PATTERN = re.compile(r'<h1[^>]*>(.*?)</h1>', re.DOTALL | re.IGNORECASE)
CONTENT_PATTERN = re.compile(r'<div[^>]*class="[^"]*post-content[^"]*"[^>]*>(.*?)</div>', re.DOTALL | re.IGNORECASE)
HTML_TAG_PATTERN = re.compile(r'<[^>]+>')
WHITESPACE_PATTERN = re.compile(r'\s+')
DATE_PATTERNS = [
    re.compile(r'(\d+)\s*分钟阅读'),
    re.compile(r'(Oct\s+\d+,\s+\d+)'),
    re.compile(r'(\d{4}-\d{2}-\d{2})'),
]

# 1. 获取文章链接
def extract_snumber_from_url(base_url: str) -> Optional[int]:
    try:
        response = requests.get(base_url)
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a')

        for link in links:
            href = link.get('href')
            if href:
                match = NEWS_ID_PATTERN.search(href)
                if match:
                    snumber = int(match.group(1))
                    return snumber
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"网络请求错误: {e}")
    except Exception as e:
        logging.error(f"提取文章链接错误: {e}")
    return None

# 2. 获取文章内容
async def extract_ai_news_article(article_id: int) -> Optional[Dict[str, Any]]:
    """使用正则表达式提取AIbase新闻文章数据"""
    
    try:
        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(
                url=f"{BASE_URL}/{article_id}",
                bypass_cache=True,
                js_code=[f"await new Promise(resolve => setTimeout(resolve, {JS_WAIT_TIME}));"],
                timeout=CRAWLER_TIMEOUT,
            )

            if not result.success:
                logging.error(f"页面爬取失败: {result.error}")
                return None

            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(result.html, 'html.parser')
            
            # 提取标题
            title_tag = soup.find('h1')
            title = title_tag.get_text().strip() if title_tag else ""
            
            # 提取内容 - 查找post-content类
            content_div = soup.find('div', class_='post-content')
            content = ""
            if content_div:
                # 获取所有文本，自动去除HTML标签
                content = content_div.get_text(separator=' ', strip=True)
            
            # 查找日期信息
            publish_date = ""
            # 尝试查找包含日期的元素
            # 可能的日期位置：meta标签、时间标签、或特定class的div
            time_tag = soup.find('time')
            if time_tag:
                publish_date = time_tag.get_text().strip()
            else:
                # 查找包含日期的meta标签
                meta_tag = soup.find('meta', property='article:published_time')
                if meta_tag and meta_tag.get('content'):
                    publish_date = meta_tag.get('content')
                else:
                    # 尝试从页面文本中提取日期（保留原有的正则方法作为备选）
                    for pattern in DATE_PATTERNS:
                        match = pattern.search(result.html)
                        if match:
                            publish_date = match.group(1)
                            break
            
            # 提取分类信息
            category = ""
            # 尝试查找分类标签
            category_tag = soup.find('a', href=lambda href: href and '/category/' in href)
            if category_tag:
                category = category_tag.get_text().strip()
            else:
                # 保留原有的分类判断作为备选
                if "AI新闻资讯" in result.html:
                    category = "AI新闻资讯"
            
            data: Dict[str, Any] = {
                "title": title,
                "content": content,
                "publish_date": publish_date,
                "category": category,
                "content_length": len(content)
            }
            
            return data
    except Exception as e:
        logging.error(f"爬取文章 {article_id} 时出错: {e}")
        return None

# 获取昨天最后一条新闻的编号
def get_yesterday_last_number(latest_number: int) -> int:
    """从昨天的JSON文件中获取最后一条新闻的news_id"""
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_file = f"{yesterday.strftime('%Y_%m_%d')}.json"
    yesterday_year = yesterday.strftime("%Y")
    yesterday_month = yesterday.strftime("%m")
    
    # 1. 优先查找按年份/月份划分的目录（新位置）
    yesterday_json_dir = os.path.join(DATA_DIR, "json", yesterday_year, yesterday_month)
    yesterday_file_path = os.path.join(yesterday_json_dir, yesterday_file)
    
    # 2. 如果新位置不存在，尝试旧的data/json目录
    if not os.path.exists(yesterday_file_path):
        yesterday_file_path = os.path.join(DATA_DIR, "json", yesterday_file)
    
    # 3. 如果还不存在，尝试脚本所在目录（最旧位置）
    if not os.path.exists(yesterday_file_path):
        yesterday_file_path = os.path.join(SCRIPT_DIR, yesterday_file)
    
    try:
        if os.path.exists(yesterday_file_path):
            with open(yesterday_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data and len(data) > 0:
                    # 获取最后一条新闻的news_id，然后+1作为今天的起始编号
                    return data[-1]['news_id'] + 1
        logging.info(f"未找到昨天的文件 {yesterday_file}，将获取最新{DEFAULT_NEWS_COUNT}条新闻")
        # 如果找不到昨天的文件，返回最新编号减去DEFAULT_NEWS_COUNT（获取最近DEFAULT_NEWS_COUNT条新闻）
        return max(1, latest_number - DEFAULT_NEWS_COUNT)  # 确保不会返回负数或0
    except FileNotFoundError:
        logging.info(f"昨天的文件 {yesterday_file} 不存在，将获取最新{DEFAULT_NEWS_COUNT}条新闻")
        return max(1, latest_number - DEFAULT_NEWS_COUNT)
    except json.JSONDecodeError as e:
        logging.error(f"解析昨天文件 {yesterday_file} 时出错: {e}，将获取最新{DEFAULT_NEWS_COUNT}条新闻")
        return max(1, latest_number - DEFAULT_NEWS_COUNT)
    except PermissionError as e:
        logging.error(f"读取昨天文件 {yesterday_file} 权限错误: {e}，将获取最新{DEFAULT_NEWS_COUNT}条新闻")
        return max(1, latest_number - DEFAULT_NEWS_COUNT)
    except Exception as e:
        logging.error(f"读取昨天文件 {yesterday_file} 时出错: {e}，将获取最新{DEFAULT_NEWS_COUNT}条新闻")
        return max(1, latest_number - DEFAULT_NEWS_COUNT)

# 生成新闻摘要
async def get_news_summary(article_data: Dict[str, Any], client: OpenAI) -> str:
    """使用OpenAI API生成新闻摘要"""
    system_prompt = """
    ## Goals
    读取并解析单条新闻文章，提炼出文章的主旨，形成一句简洁的概述。

    ## Constrains:
    概述长度150字左右，保持文章的原意和重点。

    ## Skills
    文章内容理解和总结能力。

    ## Output Format
    一句话概述，简洁明了，不超过150字。

    ## Workflow:
    1. 理解文章标题和内容
    2. 提取关键信息和主要观点
    3. 生成一句简洁的概述，不超过150字
    """

    max_retries = 3  # 最大重试次数
    base_delay = 1  # 基础延迟（秒）
    article_title = article_data['title']
    
    for attempt in range(max_retries):
        try:
            # 使用asyncio.to_thread将同步调用转换为异步
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"内容：{article_data['content']}"}
                ],
                top_p=0.7,
                temperature=0.1,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e).lower()
            error_type = "未知错误"
            
            # 详细错误类型判断
            if isinstance(e, client._exceptions.APIError):
                error_type = "API错误"
            elif isinstance(e, client._exceptions.AuthenticationError):
                error_type = "认证错误"
            elif isinstance(e, client._exceptions.PermissionError):
                error_type = "权限错误"
            elif isinstance(e, client._exceptions.RateLimitError):
                error_type = "速率限制错误"
            elif isinstance(e, client._exceptions.APIConnectionError):
                error_type = "连接错误"
            elif isinstance(e, client._exceptions.Timeout):
                error_type = "超时错误"
            elif "authentication" in error_msg or "api key" in error_msg:
                error_type = "认证错误"
            elif "rate limit" in error_msg or "quota" in error_msg:
                error_type = "速率限制错误"
            elif "timeout" in error_msg:
                error_type = "超时错误"
            elif "connection" in error_msg or "network" in error_msg:
                error_type = "网络连接错误"
            
            logging.error(f"摘要生成错误（{error_type}）：{e}，文章标题：{article_title}，尝试次数：{attempt+1}/{max_retries}")
            
            # 根据错误类型决定是否重试
            if error_type == "认证错误" or error_type == "权限错误":
                # 不可恢复的错误，直接返回
                return f"无法生成摘要：API认证/权限失败 - {article_title}"
            elif error_type == "速率限制错误" or error_type == "连接错误" or error_type == "超时错误":
                # 可恢复的错误，进行重试
                if attempt < max_retries - 1:
                    # 计算重试延迟（指数退避）
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)  # 添加随机抖动
                    logging.warning(f"API{error_type}，{delay:.2f}秒后重试（第{attempt+2}/{max_retries}次尝试），文章标题：{article_title}")
                    await asyncio.sleep(delay)
                else:
                    logging.error(f"API{error_type}，已达到最大重试次数，文章标题：{article_title}")
                    return f"无法生成摘要：API{error_type} - {article_title}"
            else:
                # 其他错误，根据尝试次数决定是否重试
                if attempt < max_retries - 1:
                    # 计算重试延迟（指数退避）
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)  # 添加随机抖动
                    logging.warning(f"摘要生成{error_type}，{delay:.2f}秒后重试（第{attempt+2}/{max_retries}次尝试），文章标题：{article_title}")
                    await asyncio.sleep(delay)
                else:
                    logging.error(f"摘要生成{error_type}，已达到最大重试次数，文章标题：{article_title}")
                    return f"无法生成摘要：{error_type} - {article_title}"

# 3. 开始提取ai咨询内容
async def main() -> None:
    logging.info("开始提取文章数据...")
    
    # 获取最新文章编号
    number = extract_snumber_from_url(BASE_URL)
    if number is None:
        logging.error("无法获取最新文章编号，程序退出")
        return
    
    # 获取当前时间并格式化为文件名
    current_time = datetime.now().strftime("%Y_%m_%d")
    
    file_name = os.path.join(JSON_DIR, f"{current_time}.json")
    
    # 从昨天的文件中获取起始编号
    yesterday_last_number = get_yesterday_last_number(number)
    
    # 并行爬取所有新闻
    logging.info(f"开始并行爬取 {number - yesterday_last_number + 1} 条新闻...")
    tasks = []
    for i in range(yesterday_last_number, number + 1):
        tasks.append(extract_ai_news_article(i))
    
    # 执行所有爬取任务
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理爬取结果
    all_news_data: List[Dict[str, Any]] = []
    for i, result in enumerate(results, start=yesterday_last_number):
        if isinstance(result, Exception):
            logging.error(f"爬取新闻 {i} 失败: {result}")
        elif result:
            result['news_id'] = i  # 添加新闻ID
            all_news_data.append(result)  # 添加到列表中
        else:
            logging.warning(f"爬取新闻 {i} 无内容")

    # 在循环结束后添加保存代码（需要更改为每天的日期作为文件名）
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(all_news_data, f, ensure_ascii=False, indent=2)

    logging.info(f"已保存 {len(all_news_data)} 条新闻到 {file_name}")
    
    # 4. 将提取好的json数据做摘要
    load_dotenv()
    api_key = os.getenv(API_KEY_ENV_VAR)
    
    # 检查API密钥是否存在
    if not api_key:
        logging.warning(f"未找到{API_KEY_ENV_VAR}环境变量，将跳过摘要生成")
        summaries = ["无法生成摘要：未配置API密钥 或密钥错误 (建议debug下密钥，有可能只是之前设置为系统变量了)"]
    else:
        # 初始化OpenAI客户端
        client = OpenAI(
            api_key=api_key,
            base_url=API_BASE_URL
        )
        
        # 生成新闻摘要 - 控制并发数量以避免API限流
        logging.info(f"开始生成 {len(all_news_data)} 条新闻摘要...")
        
        # 根据免费API限流情况，设置合适的并发数量（免费API大约每分钟允许25-30次请求）
        CONCURRENT_REQUESTS = 10  # 同时处理的请求数量，降低并发以减少429错误
        BATCH_DELAY = 5  # 每批次之间的延迟（秒），增加延迟以避免API限流
        RETRY_BATCH_DELAY = 60  # 重试批次之间的延迟（秒），给予API更多恢复时间
        
        summaries: List[str] = []
        
        # 初始化摘要列表
        for _ in range(len(all_news_data)):
            summaries.append("")
        
        # 分批处理请求
        for i in range(0, len(all_news_data), CONCURRENT_REQUESTS):
            batch_start = i
            batch_end = min(i + CONCURRENT_REQUESTS, len(all_news_data))
            batch_size = batch_end - batch_start
            
            logging.info(f"处理摘要批次 {i//CONCURRENT_REQUESTS + 1}：{batch_start + 1}-{batch_end}/{len(all_news_data)}")
            
            # 创建当前批次的任务
            batch_tasks = []
            for j in range(batch_start, batch_end):
                batch_tasks.append(get_news_summary(all_news_data[j], client))
            
            # 执行当前批次的任务
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # 处理当前批次的结果
            for j, result in enumerate(batch_results):
                idx = batch_start + j
                if isinstance(result, Exception):
                    logging.error(f"生成第 {idx+1} 条新闻摘要失败: {result}")
                    summaries[idx] = f"无法生成摘要：{all_news_data[idx]['title']}"
                else:
                    summaries[idx] = result
                
                # 将摘要添加到对应的新闻数据中
                all_news_data[idx]['summary'] = summaries[idx]
            
            # 如果不是最后一批，添加延迟
            if batch_end < len(all_news_data):
                logging.info(f"批次完成，等待 {BATCH_DELAY} 秒后继续下一批次...")
                await asyncio.sleep(BATCH_DELAY)
        
        # 重新保存包含摘要的新闻数据到JSON文件
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(all_news_data, f, ensure_ascii=False, indent=2)
        logging.info(f"已更新 {len(all_news_data)} 条新闻的摘要到 {file_name}")
        
        # 收集生成失败的摘要索引
        failed_indices = []
        for idx, summary in enumerate(summaries):
            if summary.startswith("无法生成摘要："):
                failed_indices.append(idx)
        
        # 实现失败摘要的重试机制
        max_retry_rounds = 2  # 最多重试2轮
        retry_round = 0
        
        while failed_indices and retry_round < max_retry_rounds:
            retry_round += 1
            logging.info(f"开始第 {retry_round}/{max_retry_rounds} 轮摘要重试，待重试 {len(failed_indices)} 条")
            
            # 等待更长时间，给API更多恢复时间
            logging.info(f"重试前等待 {RETRY_BATCH_DELAY} 秒...")
            await asyncio.sleep(RETRY_BATCH_DELAY)
            
            # 分批重试失败的摘要
            current_failed_indices = failed_indices.copy()
            failed_indices.clear()
            
            for i in range(0, len(current_failed_indices), CONCURRENT_REQUESTS):
                batch_start = i
                batch_end = min(i + CONCURRENT_REQUESTS, len(current_failed_indices))
                batch_size = batch_end - batch_start
                
                logging.info(f"处理重试批次 {i//CONCURRENT_REQUESTS + 1}：{batch_start + 1}-{batch_end}/{len(current_failed_indices)}")
                
                # 创建当前批次的重试任务
                batch_tasks = []
                for j in range(batch_start, batch_end):
                    actual_idx = current_failed_indices[j]
                    batch_tasks.append(get_news_summary(all_news_data[actual_idx], client))
                
                # 执行当前批次的重试任务
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # 处理当前批次的重试结果
                for j, result in enumerate(batch_results):
                    actual_idx = current_failed_indices[batch_start + j]
                    if isinstance(result, Exception):
                        logging.error(f"第 {retry_round} 轮重试：生成第 {actual_idx+1} 条新闻摘要仍失败: {result}")
                        failed_indices.append(actual_idx)  # 保留到下一轮重试
                    else:
                        logging.info(f"第 {retry_round} 轮重试：生成第 {actual_idx+1} 条新闻摘要成功")
                        summaries[actual_idx] = result
                        all_news_data[actual_idx]['summary'] = result
                
                # 如果不是最后一批，添加延迟
                if batch_end < len(current_failed_indices):
                    logging.info(f"重试批次完成，等待 {BATCH_DELAY} 秒后继续下一批次...")
                    await asyncio.sleep(BATCH_DELAY)
            
            # 保存当前重试结果到JSON文件
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(all_news_data, f, ensure_ascii=False, indent=2)
            logging.info(f"已更新第 {retry_round} 轮重试后的摘要到 {file_name}")
        
        if failed_indices:
            logging.warning(f"摘要生成完成，但仍有 {len(failed_indices)} 条无法生成摘要")
        else:
            logging.info("所有摘要生成成功！")
    
    # 将摘要好的数据写入到一个 .txt文件中
    txt_file_name = os.path.join(TXT_DIR, f"{current_time}_news_data.txt")
    with open(txt_file_name, 'w', encoding='utf-8') as f:
        # 写入所有摘要，每条摘要占一行
        for summary in summaries:
            f.write(summary + "\n\n")

# 运行
if __name__ == "__main__":
    asyncio.run(main())

