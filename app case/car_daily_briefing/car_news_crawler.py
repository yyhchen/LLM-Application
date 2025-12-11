#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立汽车新闻爬虫
目标：汽车之家新闻频道
"""
import re
import logging
import os
import json
import time
import random
from typing import List, Dict, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
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

logger = logging.getLogger(__name__)


class CarNewsCrawler:
    """
    独立汽车新闻爬虫
    主要爬取汽车之家新闻频道的新闻
    """
    
    BASE_URL = "https://www.autohome.com.cn"
    NEWS_URL = "https://www.autohome.com.cn/news/"
    SOURCE_NAME = "autohome"
    
    def __init__(self):
        """初始化爬虫"""
        self.session = requests.Session()
        
        # 动态User-Agent池，模拟不同浏览器
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/114.0.1823.51",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        ]
        
        # 设置初始请求头，后续会动态更新User-Agent
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })
        
        # 配置项
        self.timeout = 15  # 增加超时时间，提高稳定性
        self.max_retries = 3  # 最大重试次数
        
        # 延时配置，用于反爬
        self.min_sleep_time = 1  # 最小延时时间（秒）
        self.max_sleep_time = 3  # 最大延时时间（秒）
        self.min_retry_sleep_time = 3  # 重试时最小延时时间（秒）
        self.max_retry_sleep_time = 5  # 重试时最大延时时间（秒）
        
        # 数据目录结构配置
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.script_dir, "data")
        
        # 获取当前年份和月份
        self.current_year = datetime.now().strftime("%Y")
        self.current_month = datetime.now().strftime("%m")
        
        # 按年份/月份划分的目录
        self.json_dir = os.path.join(self.data_dir, "json", self.current_year, self.current_month)
        self.txt_dir = os.path.join(self.data_dir, "txt", self.current_year, self.current_month)
        
        # 确保目录存在
        os.makedirs(self.json_dir, exist_ok=True)
        os.makedirs(self.txt_dir, exist_ok=True)
        
        # 新闻摘要配置
        self.api_base_url = "https://api.longcat.chat/openai"  # API基础URL
        self.model_name = "LongCat-Flash-Chat"  # 模型名称
        self.api_key_env_var = "MEITUAN_API_KEY"  # API密钥环境变量
        self.max_summary_retries = 3  # 摘要生成最大重试次数
        self.base_summary_delay = 1  # 摘要生成基础延迟（秒）
    
    def _update_user_agent(self) -> None:
        """动态更新User-Agent，提高反爬能力"""
        user_agent = random.choice(self.user_agents)
        self.session.headers.update({"User-Agent": user_agent})
    
    def crawl(self, max_news: int = 30) -> List[Dict]:
        """
        爬取汽车新闻
        
        Args:
            max_news: 最大爬取新闻数量，防止爬取过多被限制IP
            
        Returns:
            新闻列表
        """
        logger.info(f"开始爬取{self.SOURCE_NAME}，最多爬取{max_news}条新闻")
        
        news_list = []
        
        try:
            # 更新User-Agent
            self._update_user_agent()
            
            # 获取新闻列表
            news_links = self._get_news_links()
            logger.info(f"获取到{len(news_links)}条新闻链接")
            
            # 检查新闻链接数量
            if len(news_links) < max_news:
                logger.warning(f"只获取到{len(news_links)}条新闻链接，少于请求的{max_news}条")
                max_news = len(news_links)  # 调整实际爬取数量
            
            # 限制爬取数量
            for i, link in enumerate(news_links[:max_news], 1):
                try:
                    logger.info(f"正在爬取第{i}/{max_news}条新闻...")
                    
                    # 智能延时，模拟人类阅读间隔
                    sleep_time = random.uniform(self.min_sleep_time, self.max_sleep_time)
                    logger.info(f"等待 {sleep_time:.2f} 秒后开始爬取...")
                    time.sleep(sleep_time)
                    
                    # 动态更新User-Agent，进一步提高反爬能力
                    self._update_user_agent()
                    
                    # 获取新闻详情，支持重试
                    news_item = None
                    for retry in range(self.max_retries):
                        try:
                            news_item = self._get_news_detail(link)
                            if news_item:
                                break
                            else:
                                logger.warning(f"第{retry+1}/{self.max_retries}次尝试获取新闻详情失败，内容为空")
                        except Exception as e:
                            logger.warning(f"第{retry+1}/{self.max_retries}次尝试获取新闻详情失败：{e}")
                        
                        # 重试时增加延时
                        if retry < self.max_retries - 1:
                            retry_sleep_time = random.uniform(self.min_retry_sleep_time, self.max_retry_sleep_time)
                            logger.info(f"重试等待 {retry_sleep_time:.2f} 秒后继续...")
                            time.sleep(retry_sleep_time)
                    
                    if news_item:
                        news_list.append(news_item)
                        logger.info(f"成功爬取新闻：{news_item['title']}")
                    else:
                        logger.warning(f"多次尝试后仍无法获取新闻详情：{link}")
                except Exception as e:
                    logger.error(f"爬取新闻详情时发生未知错误：{e}")
                    # 发生未知错误时，增加延时后继续
                    time.sleep(random.uniform(self.min_retry_sleep_time, self.max_retry_sleep_time))
                    continue
        except Exception as e:
            logger.error(f"爬取{self.SOURCE_NAME}失败：{e}")
        
        logger.info(f"爬取完成，共获取{len(news_list)}条新闻")
        return news_list
    
    def _get_news_links(self) -> List[str]:
        """
        获取新闻列表链接
        
        Returns:
            新闻链接列表
        """
        news_links = []
        
        try:
            response = self.session.get(self.NEWS_URL, timeout=self.timeout)
            response.raise_for_status()
            
            # 优化编码处理，使用chardet自动检测编码
            import chardet
            detected_encoding = chardet.detect(response.content)['encoding']
            logger.debug(f"检测到编码：{detected_encoding}")
            
            # 使用检测到的编码，若检测失败则使用gbk作为 fallback
            response.encoding = detected_encoding or 'gbk'
            
            # 直接使用response.content解码，确保编码正确
            html_content = response.content.decode(response.encoding, errors='replace')
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 查找新闻链接，汽车之家新闻频道的新闻链接通常在特定的class中
            # 主要新闻区域
            main_news = soup.find('div', class_='news-wrap')
            if main_news:
                links = main_news.find_all('a', href=True)
                for link in links:
                    href = link.get('href')
                    # 过滤出新闻链接，汽车之家的新闻链接通常以/news/开头
                    if href and '/news/' in href:
                        # 补全绝对URL，但避免重复拼接
                        if href.startswith('http'):
                            # 已经是完整URL，直接使用
                            full_url = href
                        elif href.startswith('//'):
                            # 协议相对URL，添加https:
                            full_url = 'https:' + href
                        elif href.startswith('/'):
                            # 相对URL，拼接BASE_URL
                            full_url = self.BASE_URL + href
                        else:
                            # 其他相对路径，暂不处理
                            continue
                        # 去重
                        if full_url not in news_links:
                            news_links.append(full_url)
            
            # 新闻列表区域
            news_list = soup.find('ul', class_='article')
            if news_list:
                links = news_list.find_all('a', href=True)
                for link in links:
                    href = link.get('href')
                    if href and '/news/' in href:
                        # 补全绝对URL，但避免重复拼接
                        if href.startswith('http'):
                            # 已经是完整URL，直接使用
                            full_url = href
                        elif href.startswith('//'):
                            # 协议相对URL，添加https:
                            full_url = 'https:' + href
                        elif href.startswith('/'):
                            # 相对URL，拼接BASE_URL
                            full_url = self.BASE_URL + href
                        else:
                            # 其他相对路径，暂不处理
                            continue
                        if full_url not in news_links:
                            news_links.append(full_url)
        except Exception as e:
            logger.error(f"获取新闻列表失败：{e}")
        
        return news_links
    
    def _get_news_detail(self, url: str) -> Optional[Dict]:
        """
        获取新闻详情
        
        Args:
            url: 新闻详情页URL
            
        Returns:
            新闻详情字典
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # 优化编码处理，使用chardet自动检测编码
            import chardet
            detected_encoding = chardet.detect(response.content)['encoding']
            logger.debug(f"检测到编码：{detected_encoding}")
            
            # 使用检测到的编码，若检测失败则使用gbk作为 fallback
            response.encoding = detected_encoding or 'gbk'
            
            # 直接使用response.content解码，确保编码正确
            html_content = response.content.decode(response.encoding, errors='replace')
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取标题
            title = self._extract_title(soup)
            logger.debug(f"提取到标题：{title}")
            if not title:
                logger.warning(f"无法提取标题：{url}")
                return None
            
            # 提取发布时间
            publish_time = self._extract_publish_time(soup)
            logger.debug(f"提取到发布时间：{publish_time}")
            
            # 提取作者
            author = self._extract_author(soup)
            logger.debug(f"提取到作者：{author}")
            
            # 提取内容
            content = self._extract_content(soup)
            logger.debug(f"提取到内容长度：{len(content)}")
            if not content:
                logger.warning(f"无法提取内容：{url}")
                # 不直接返回None，继续构建新闻对象，以便调试
            
            # 构建新闻字典
            news_item = {
                'title': title,
                'url': url,
                'source': self.SOURCE_NAME,
                'publish_time': publish_time,
                'author': author,
                'content': content
            }
            
            return news_item
        except Exception as e:
            logger.warning(f"获取新闻详情失败：{e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """
        提取新闻标题
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            新闻标题
        """
        # 汽车之家的标题通常在h1标签中
        title_tag = soup.find('h1')
        if title_tag:
            return title_tag.get_text().strip()
        
        # 备选方案：查找meta标签中的标题
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            return meta_title.get('content').strip()
        
        return ""
    
    def _extract_publish_time(self, soup: BeautifulSoup) -> datetime:
        """
        提取发布时间
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            发布时间
        """
        try:
            # 汽车之家的发布时间通常在特定的class中
            time_tag = soup.find('div', class_='article-info')
            if time_tag:
                time_str = time_tag.get_text().strip()
                # 提取时间字符串，格式如：2023-10-01 14:30
                time_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}', time_str)
                if time_match:
                    time_str = time_match.group()
                    return datetime.strptime(time_str, '%Y-%m-%d %H:%M')
            
            # 备选方案：查找所有包含时间的标签
            time_tag = soup.find(text=re.compile(r'\d{4}-\d{2}-\d{2}'))
            if time_tag:
                time_str = time_tag.strip()
                # 提取时间字符串
                time_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}', time_str)
                if time_match:
                    time_str = time_match.group()
                    return datetime.strptime(time_str, '%Y-%m-%d %H:%M')
                else:
                    return datetime.strptime(time_str, '%Y-%m-%d')
        except Exception as e:
            logger.debug(f"提取发布时间失败：{e}")
        
        return datetime.now()
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """
        提取作者
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            作者
        """
        try:
            # 汽车之家的作者通常在article-info类中
            info_tag = soup.find('div', class_='article-info')
            if info_tag:
                info_text = info_tag.get_text().strip()
                # 提取作者信息，格式如：作者：XXX
                author_match = re.search(r'作者：(.*?)\s', info_text)
                if author_match:
                    return author_match.group(1).strip()
            
            # 备选方案：查找meta标签中的作者
            meta_author = soup.find('meta', name='author')
            if meta_author and meta_author.get('content'):
                return meta_author.get('content').strip()
        except Exception as e:
            logger.debug(f"提取作者失败：{e}")
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """
        提取新闻内容
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            新闻内容
        """
        content = ""
        
        try:
            # 调试：查看页面中所有div标签的id和class
            logger.debug("=== 调试：页面中的div标签信息 ===")
            div_tags = soup.find_all('div', limit=20)  # 只查看前20个div标签
            for i, div in enumerate(div_tags):
                div_id = div.get('id') or '无'
                div_class = div.get('class') or '无'
                logger.debug(f"div {i+1}: id={div_id}, class={div_class}")
            
            # 尝试多种方式提取内容
            # 1. 查找id为articleContent的标签
            content_tag = soup.find('div', id='articleContent')
            if content_tag:
                logger.debug("找到id为articleContent的标签")
                paragraphs = content_tag.find_all('p')
                logger.debug(f"找到{len(paragraphs)}个p标签")
                if paragraphs:
                    filtered_paragraphs = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
                    if filtered_paragraphs:
                        content = '\n'.join(filtered_paragraphs)
            
            # 2. 查找class为articleContent的标签
            if not content:
                content_tag = soup.find('div', class_='articleContent')
                if content_tag:
                    logger.debug("找到class为articleContent的标签")
                    paragraphs = content_tag.find_all('p')
                    logger.debug(f"找到{len(paragraphs)}个p标签")
                    if paragraphs:
                        filtered_paragraphs = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
                        if filtered_paragraphs:
                            content = '\n'.join(filtered_paragraphs)
            
            # 3. 查找class包含content的标签
            if not content:
                content_tags = soup.find_all('div', class_=re.compile(r'content'))
                for tag in content_tags:
                    paragraphs = tag.find_all('p')
                    if paragraphs:
                        filtered_paragraphs = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
                        if filtered_paragraphs:
                            content = '\n'.join(filtered_paragraphs)
                            logger.debug(f"从class包含content的标签中提取到内容")
                            break
            
            # 4. 查找class为artContent的标签（汽车之家常用的正文class）
            if not content:
                content_tag = soup.find('div', class_='artContent')
                if content_tag:
                    logger.debug("找到class为artContent的标签")
                    paragraphs = content_tag.find_all('p')
                    logger.debug(f"找到{len(paragraphs)}个p标签")
                    if paragraphs:
                        filtered_paragraphs = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
                        if filtered_paragraphs:
                            content = '\n'.join(filtered_paragraphs)
            
            # 5. 直接从body中提取所有p标签
            if not content:
                all_paragraphs = soup.find_all('p')
                logger.debug(f"直接找到{len(all_paragraphs)}个p标签")
                if all_paragraphs:
                    filtered_paragraphs = []
                    for p in all_paragraphs[:30]:  # 只查看前30个p标签
                        p_text = p.get_text().strip()
                        if p_text and len(p_text) > 20:  # 过滤掉短文本
                            filtered_paragraphs.append(p_text)
                    if filtered_paragraphs:
                        content = '\n'.join(filtered_paragraphs[:10])  # 只保留前10段
        except Exception as e:
            logger.error(f"提取新闻内容失败：{e}")
        
        logger.debug(f"最终提取到的内容长度：{len(content)}")
        return content
    
    def _get_news_summary(self, article_data: Dict, client: OpenAI) -> str:
        """
        使用OpenAI API生成新闻摘要
        
        Args:
            article_data: 新闻数据字典
            client: OpenAI客户端实例
            
        Returns:
            新闻摘要
        """
        system_prompt = """
        ## Goals
        读取并解析单条汽车新闻文章，提炼出文章的主旨，形成一句简洁的概述。

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

        for attempt in range(self.max_summary_retries):
            try:
                # 调用OpenAI API生成摘要
                response = client.chat.completions.create(
                    model=self.model_name,
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
                if "authentication" in error_msg or "api key" in error_msg:
                    logger.error(f"API认证错误: {e}")
                    return f"无法生成摘要：API认证失败 - {article_data['title']}"
                elif "rate limit" in error_msg or "quota" in error_msg:
                    if attempt < self.max_summary_retries - 1:
                        # 计算重试延迟（指数退避）
                        delay = self.base_summary_delay * (2 ** attempt) + random.uniform(0, 1)  # 添加随机抖动
                        logger.warning(f"API速率限制，{delay:.2f}秒后重试（第{attempt+2}/{self.max_summary_retries}次尝试）")
                        time.sleep(delay)
                    else:
                        logger.error(f"API速率限制错误，已达到最大重试次数: {e}")
                        return f"无法生成摘要：API请求频率过高 - {article_data['title']}"
                else:
                    logger.error(f"摘要生成错误: {e}")
                    return f"无法生成摘要：{article_data['title']}"
    
    def _save_news(self, news_list: List[Dict]) -> None:
        """
        保存新闻数据到文件
        
        Args:
            news_list: 新闻列表
        """
        if not news_list:
            logger.warning("没有新闻数据可保存")
            return
        
        # 获取当前时间并格式化为文件名
        current_time = datetime.now().strftime("%Y_%m_%d")
        
        # 1. 生成新闻摘要
        load_dotenv()
        api_key = os.getenv(self.api_key_env_var)
        
        summaries = []
        
        if not api_key:
            logger.warning(f"未找到{self.api_key_env_var}环境变量，将跳过摘要生成")
            summaries = ["无法生成摘要：未配置API密钥或密钥错误"] * len(news_list)
            # 为每条新闻添加摘要字段
            for i, news in enumerate(news_list):
                news['summary'] = summaries[i]
        else:
            # 初始化OpenAI客户端
            client = OpenAI(
                api_key=api_key,
                base_url=self.api_base_url
            )
            
            # 生成新闻摘要
            logger.info(f"开始生成 {len(news_list)} 条新闻摘要...")
            
            for i, news in enumerate(news_list):
                logger.info(f"正在生成第 {i+1}/{len(news_list)} 条新闻摘要...")
                summary = self._get_news_summary(news, client)
                summaries.append(summary)
                news['summary'] = summary
            
            logger.info(f"摘要生成完成")
        
        # 2. 保存为JSON格式
        json_file_name = os.path.join(self.json_dir, f"{current_time}.json")
        try:
            with open(json_file_name, 'w', encoding='utf-8') as f:
                json.dump(news_list, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"已保存{len(news_list)}条新闻到{json_file_name}")
        except Exception as e:
            logger.error(f"保存JSON文件失败：{e}")
        
        # 3. 保存为TXT格式
        txt_file_name = os.path.join(self.txt_dir, f"{current_time}_news.txt")
        try:
            with open(txt_file_name, 'w', encoding='utf-8') as f:
                for i, (news, summary) in enumerate(zip(news_list, summaries), 1):
                    f.write(f"{'='*50}\n")
                    f.write(f"新闻{i}：\n")
                    f.write(f"{'='*50}\n")
                    f.write(f"标题：{news['title']}\n")
                    f.write(f"来源：{news['source']}\n")
                    f.write(f"发布时间：{news['publish_time']}\n")
                    f.write(f"作者：{news['author'] if news['author'] else '未知'}\n")
                    f.write(f"链接：{news['url']}\n")
                    f.write(f"{'='*20} 摘要 {'='*20}\n")
                    f.write(f"{summary}\n")
                    f.write(f"{'='*20} 内容 {'='*20}\n")
                    f.write(f"{news['content']}\n")
                    f.write(f"{'='*50}\n\n")
            logger.info(f"已保存{len(news_list)}条新闻到{txt_file_name}")
        except Exception as e:
            logger.error(f"保存TXT文件失败：{e}")


if __name__ == "__main__":
    # 测试爬虫
    crawler = CarNewsCrawler()
    news_list = crawler.crawl(max_news=30)  # 只爬取5条新闻，防止被限制IP
    
    # 保存新闻数据
    crawler._save_news(news_list)
    
    # 打印爬取结果
    print("\n" + "="*50)
    print(f"爬取结果：共{len(news_list)}条新闻")
    print("="*50)
    
    for i, news in enumerate(news_list, 1):
        print(f"\n新闻{i}：")
        print(f"标题：{news['title']}")
        print(f"来源：{news['source']}")
        print(f"发布时间：{news['publish_time']}")
        print(f"作者：{news['author']}")
        print(f"链接：{news['url']}")
        print(f"内容：{news['content'][:100]}...")
        print("-"*50)
