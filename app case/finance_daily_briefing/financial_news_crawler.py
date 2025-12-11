#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立财经新闻爬虫
目标：新浪财经股票频道
"""
import re
import logging
import os
import json
from typing import List, Dict, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class FinancialNewsCrawler:
    """
    独立财经新闻爬虫
    主要爬取新浪财经股票频道的新闻
    """
    
    BASE_URL = "https://finance.sina.com.cn"
    STOCK_URL = "https://finance.sina.com.cn/stock/"
    SOURCE_NAME = "sina_finance"
    
    def __init__(self):
        """初始化爬虫"""
        self.session = requests.Session()
        # 设置合理的请求头，模拟浏览器
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })
        # 设置超时时间
        self.timeout = 10
        
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
    
    def crawl(self, max_news: int = 5) -> List[Dict]:
        """
        爬取财经新闻
        
        Args:
            max_news: 最大爬取新闻数量，防止爬取过多被限制IP
            
        Returns:
            新闻列表
        """
        logger.info(f"开始爬取{self.SOURCE_NAME}，最多爬取{max_news}条新闻")
        
        news_list = []
        
        try:
            # 获取新闻列表
            news_links = self._get_news_links()
            logger.info(f"获取到{len(news_links)}条新闻链接")
            
            # 限制爬取数量
            for link in news_links[:max_news]:
                try:
                    # 获取新闻详情
                    news_item = self._get_news_detail(link)
                    if news_item:
                        news_list.append(news_item)
                        logger.info(f"成功爬取新闻：{news_item['title']}")
                except Exception as e:
                    logger.warning(f"爬取新闻详情失败：{e}")
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
            response = self.session.get(self.STOCK_URL, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找新闻链接，新浪财经股票频道的新闻链接通常在特定的class中
            # 这里使用多种可能的选择器，提高兼容性
            news_containers = soup.find_all(['div', 'ul'], class_=re.compile(r'news|list|feed'))
            
            for container in news_containers:
                # 查找所有a标签
                links = container.find_all('a', href=True)
                for link in links:
                    href = link.get('href')
                    # 过滤出股票相关的新闻链接
                    if href and '/stock/' in href and href.startswith('https://'):
                        # 去重
                        if href not in news_links:
                            news_links.append(href)
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
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取标题
            title = self._extract_title(soup)
            if not title:
                return None
            
            # 提取发布时间
            publish_time = self._extract_publish_time(soup)
            
            # 提取作者
            author = self._extract_author(soup)
            
            # 提取内容
            content = self._extract_content(soup)
            if not content:
                return None
            
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
        # 新浪财经的标题通常在h1标签中
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
            # 新浪财经的发布时间通常在特定的class中
            time_tag = soup.find('span', class_=re.compile(r'time|date|publish'))
            if not time_tag:
                # 查找所有包含时间的标签
                time_tag = soup.find(text=re.compile(r'\d{4}-\d{2}-\d{2}'))
                if time_tag:
                    time_str = time_tag.strip()
                else:
                    return datetime.now()
            else:
                time_str = time_tag.get_text().strip()
            
            # 清洗时间字符串，只保留日期和时间部分
            time_str = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}', time_str)
            if time_str:
                time_str = time_str.group()
            else:
                return datetime.now()
            
            # 解析时间
            if len(time_str) == 10:
                # 只有日期，没有时间
                return datetime.strptime(time_str, '%Y-%m-%d')
            else:
                # 有日期和时间
                return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
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
            # 新浪财经的作者通常在特定的class中
            author_tag = soup.find('span', class_=re.compile(r'author|source|from'))
            if author_tag:
                author = author_tag.get_text().strip()
                # 清洗作者信息，移除不必要的前缀
                author = re.sub(r'来源：|作者：|编辑：', '', author)
                return author
            
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
            # 新浪财经的正文通常在id为artibody或article的标签中
            content_tags = soup.find_all(['div', 'article'], id=re.compile(r'artibody|article'))
            
            if not content_tags:
                # 备选方案：查找class包含content或article的标签
                content_tags = soup.find_all(['div', 'article'], class_=re.compile(r'content|article'))
            
            for tag in content_tags:
                # 提取所有p标签内容
                paragraphs = tag.find_all('p')
                if paragraphs:
                    # 过滤掉广告和无关内容
                    filtered_paragraphs = []
                    for p in paragraphs:
                        p_text = p.get_text().strip()
                        if p_text and not any(keyword in p_text for keyword in ['广告', '免责声明', '新浪财经', '炒股大赛']):
                            filtered_paragraphs.append(p_text)
                    
                    if filtered_paragraphs:
                        content = '\n'.join(filtered_paragraphs)
                        break
        except Exception as e:
            logger.debug(f"提取新闻内容失败：{e}")
        
        return content
    
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
        
        # 1. 保存为JSON格式
        json_file_name = os.path.join(self.json_dir, f"{current_time}.json")
        try:
            with open(json_file_name, 'w', encoding='utf-8') as f:
                json.dump(news_list, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"已保存{len(news_list)}条新闻到{json_file_name}")
        except Exception as e:
            logger.error(f"保存JSON文件失败：{e}")
        
        # 2. 保存为TXT格式
        txt_file_name = os.path.join(self.txt_dir, f"{current_time}_news.txt")
        try:
            with open(txt_file_name, 'w', encoding='utf-8') as f:
                for i, news in enumerate(news_list, 1):
                    f.write(f"{'='*50}\n")
                    f.write(f"新闻{i}：\n")
                    f.write(f"{'='*50}\n")
                    f.write(f"标题：{news['title']}\n")
                    f.write(f"来源：{news['source']}\n")
                    f.write(f"发布时间：{news['publish_time']}\n")
                    f.write(f"作者：{news['author'] if news['author'] else '未知'}\n")
                    f.write(f"链接：{news['url']}\n")
                    f.write(f"{'='*20} 内容 {'='*20}\n")
                    f.write(f"{news['content']}\n")
                    f.write(f"{'='*50}\n\n")
            logger.info(f"已保存{len(news_list)}条新闻到{txt_file_name}")
        except Exception as e:
            logger.error(f"保存TXT文件失败：{e}")


if __name__ == "__main__":
    # 测试爬虫
    crawler = FinancialNewsCrawler()
    news_list = crawler.crawl(max_news=5)  # 只爬取5条新闻，防止被限制IP
    
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
