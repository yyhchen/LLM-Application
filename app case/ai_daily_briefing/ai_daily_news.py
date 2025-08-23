import requests
from bs4 import BeautifulSoup
import re
import json
import asyncio
import os
from crawl4ai import AsyncWebCrawler
from datetime import datetime, timedelta
from openai import OpenAI
from dotenv import load_dotenv

# 1. 获取文章链接
def extract_snumber_from_url(base_url):
    try:
        response = requests.get(base_url)
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a')

        for link in links:
            href = link.get('href')
            if href:
                pattern = r'/news/(\d+)' 
                match = re.search(pattern, href)
                if match:
                    snumber = int(match.group(1))
                    return snumber
        return None
    except Exception as e:
        print(f"error: {e}")
    return None

# 2. 获取文章内容
async def extract_ai_news_article(article_id):
    """使用正则表达式提取AIbase新闻文章数据"""
    
    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(
            url=f"https://www.aibase.com/zh/news/{article_id}",
            bypass_cache=True,
            js_code=["await new Promise(resolve => setTimeout(resolve, 5000));"],
            timeout=30000,
        )

        if not result.success:
            print(f"页面爬取失败: {result.error}")
            return None

        html = result.html
        
        # 提取标题
        title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL | re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else ""
        
        # 提取内容 - 查找post-content类
        content_pattern = r'<div[^>]*class="[^"]*post-content[^"]*"[^>]*>(.*?)</div>'
        content_match = re.search(content_pattern, html, re.DOTALL | re.IGNORECASE)
        
        if content_match:
            content_html = content_match.group(1)
            # 移除HTML标签
            content = re.sub(r'<[^>]+>', '', content_html)
            content = re.sub(r'\s+', ' ', content).strip()
        else:
            content = ""
        
        # 查找日期信息
        date_patterns = [
            r'(\d+)\s*分钟阅读',
            r'(Oct\s+\d+,\s+\d+)',
            r'(\d{4}-\d{2}-\d{2})',
        ]
        
        publish_date = ""
        for pattern in date_patterns:
            match = re.search(pattern, html)
            if match:
                publish_date = match.group(1)
                break
        
        # 提取分类信息
        category = ""
        if "AI新闻资讯" in html:
            category = "AI新闻资讯"
        
        data = {
            "title": title,
            "content": content,
            "publish_date": publish_date,
            "category": category,
            "content_length": len(content)
        }
        
        return data

# 获取昨天最后一条新闻的编号
def get_yesterday_last_number():
    """从昨天的JSON文件中获取最后一条新闻的news_id"""
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_file = f"{yesterday.strftime('%Y_%m_%d')}.json"
    
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yesterday_file_path = os.path.join(current_dir, yesterday_file)
    
    try:
        if os.path.exists(yesterday_file_path):
            with open(yesterday_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data and len(data) > 0:
                    # 获取最后一条新闻的news_id，然后+1作为今天的起始编号
                    return data[-1]['news_id'] + 1
        print(f"未找到昨天的文件 {yesterday_file}，使用默认起始编号 20737")
        return 20737
    except Exception as e:
        print(f"读取昨天文件时出错: {e}，使用默认起始编号 20737")
        return 20737

# 3. 开始提取ai咨询内容
async def main():
    print("开始提取文章数据...")
    
    # 获取最新文章编号
    number = extract_snumber_from_url("https://www.aibase.com/zh/news")
    
    # 获取当前时间并格式化为文件名
    current_time = datetime.now().strftime("%Y_%m_%d")
    
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_name = os.path.join(current_dir, f"{current_time}.json")
    
    # 从昨天的文件中获取起始编号
    yesterday_last_number = get_yesterday_last_number()
    all_news_data = []  # 添加这行来存储所有数据
    
    for i in range(yesterday_last_number, number + 1):
        print(f"正在提取咨询编号: {i}")
        article_data = await extract_ai_news_article(i)
        
        if article_data:  # 添加这个检查
            article_data['news_id'] = i  # 添加新闻ID
            all_news_data.append(article_data)  # 添加到列表中

    # 在循环结束后添加保存代码（需要更改为每天的日期作为文件名）
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(all_news_data, f, ensure_ascii=False, indent=2)

    print(f"已保存 {len(all_news_data)} 条新闻到 {file_name}")
    
    # 4. 将提取好的json数据做摘要
    load_dotenv()
    api_key = os.getenv("ZHIPU_API_KEY")
    
    # 检查API密钥是否存在
    if not api_key:
        print("警告: 未找到ZHIPU_API_KEY环境变量，将跳过摘要生成")
        summaries = ["无法生成摘要：未配置API密钥 或密钥错误 (建议debug下密钥，有可能只是之前设置为系统变量了)"]
    else:
        def get_news_summary(article_data):
            client = OpenAI(
                api_key=api_key,
                base_url="https://open.bigmodel.cn/api/paas/v4/"
            )

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

            try:
                response = client.chat.completions.create(
                    model="glm-4.5-flash",
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
                print(f"摘要生成错误: {e}")
                return f"无法生成摘要：{article_data['title']}"
        
        # 为每条新闻生成摘要
        summaries = []
        for i, article in enumerate(all_news_data):
            print(f"正在生成第 {i+1}/{len(all_news_data)} 条新闻摘要...")
            summary = get_news_summary(article)
            summaries.append(summary)
    
    # 将摘要好的数据写入到一个 .txt文件中
    txt_file_name = os.path.join(current_dir, f"{current_time}_news_data.txt")
    with open(txt_file_name, 'w', encoding='utf-8') as f:
        # 写入所有摘要，每条摘要占一行
        for summary in summaries:
            f.write(summary + "\n\n")

# 运行
if __name__ == "__main__":
    asyncio.run(main())

