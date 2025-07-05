#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频收集器 - Selenium版本
使用浏览器自动化模拟真实用户操作
"""

import time
import random
import csv
import re
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BilibiliSeleniumCollector:
    """使用Selenium的B站视频收集器"""
    
    def __init__(self, headless: bool = False, proxy: Optional[str] = None):
        """
        初始化收集器
        
        Args:
            headless: 是否使用无头模式
            proxy: 代理服务器地址 (格式: "ip:port")
        """
        self.driver = None
        self.headless = headless
        self.proxy = proxy
        self.wait_time = 10
        
    def _setup_driver(self):
        """设置Chrome浏览器驱动"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # 添加反检测参数
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 设置用户代理
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
        
        # 设置代理
        if self.proxy:
            chrome_options.add_argument(f"--proxy-server={self.proxy}")
        
        # 设置窗口大小
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            # 执行JavaScript来隐藏webdriver属性
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(5)
            logger.info("Chrome浏览器启动成功")
        except Exception as e:
            logger.error(f"启动Chrome浏览器失败: {e}")
            raise
    
    def _random_delay(self, min_delay=2, max_delay=5):
        """随机延迟"""
        delay = random.uniform(min_delay, max_delay)
        logger.info(f"随机延迟 {delay:.2f} 秒...")
        time.sleep(delay)
    
    def _scroll_page(self, scroll_times=3):
        """模拟页面滚动"""
        for i in range(scroll_times):
            scroll_height = random.randint(300, 800)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_height});")
            time.sleep(random.uniform(0.5, 1.5))
    
    def get_uid_from_url(self, url: str) -> Optional[str]:
        """从UP主主页URL中提取UID"""
        patterns = [
            r'space\.bilibili\.com/(\d+)',
            r'uid=(\d+)',
            r'/(\d+)/?$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def collect_videos_from_page(self, page_url: str, max_videos: int = 100) -> List[Dict]:
        """从单个页面收集视频信息"""
        videos = []
        
        try:
            logger.info(f"正在访问页面: {page_url}")
            self.driver.get(page_url)
            self._random_delay(3, 6)
            
            # 等待页面加载
            WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".video-list .video-item, .bili-video-card"))
            )
            
            # 模拟页面滚动
            self._scroll_page()
            
            # 查找视频元素
            video_selectors = [
                ".video-list .video-item",
                ".bili-video-card",
                ".bili-video-card__info",
                "[data-aid]"
            ]
            
            video_elements = []
            for selector in video_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        video_elements = elements
                        logger.info(f"找到 {len(elements)} 个视频元素 (使用选择器: {selector})")
                        break
                except:
                    continue
            
            if not video_elements:
                logger.warning("未找到视频元素")
                return videos
            
            # 提取视频信息
            for i, element in enumerate(video_elements[:max_videos]):
                try:
                    video_info = self._extract_video_info(element)
                    if video_info:
                        videos.append(video_info)
                        logger.info(f"提取视频 {i+1}: {video_info.get('title', 'Unknown')}")
                except Exception as e:
                    logger.error(f"提取视频信息失败: {e}")
                    continue
                
                # 随机延迟
                if i % 5 == 0:  # 每5个视频延迟一次
                    self._random_delay(1, 3)
            
        except TimeoutException:
            logger.error("页面加载超时")
        except Exception as e:
            logger.error(f"收集视频时出错: {e}")
        
        return videos
    
    def _extract_video_info(self, element) -> Optional[Dict]:
        """从视频元素中提取信息"""
        try:
            # 尝试多种方式提取信息
            title = ""
            bvid = ""
            video_url = ""
            
            # 提取标题
            title_selectors = [
                ".title",
                ".bili-video-card__info--tit",
                "h3",
                ".video-title"
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, selector)
                    title = title_elem.get_attribute("title") or title_elem.text
                    if title:
                        break
                except:
                    continue
            
            # 提取链接和BVID
            link_selectors = [
                "a[href*='/video/']",
                ".bili-video-card__info--tit a",
                "a"
            ]
            
            for selector in link_selectors:
                try:
                    link_elem = element.find_element(By.CSS_SELECTOR, selector)
                    href = link_elem.get_attribute("href")
                    if href and "/video/" in href:
                        video_url = href
                        # 提取BVID
                        bvid_match = re.search(r'/video/(BV\w+)', href)
                        if bvid_match:
                            bvid = bvid_match.group(1)
                        break
                except:
                    continue
            
            # 提取其他信息
            view_count = ""
            duration = ""
            
            try:
                view_elem = element.find_element(By.CSS_SELECTOR, ".play, .view, .bili-video-card__stats--item")
                view_count = view_elem.text
            except:
                pass
            
            try:
                duration_elem = element.find_element(By.CSS_SELECTOR, ".duration, .bili-video-card__info--duration")
                duration = duration_elem.text
            except:
                pass
            
            if title and video_url:
                return {
                    'bvid': bvid,
                    'title': title.strip(),
                    'video_url': video_url,
                    'view_count': view_count.strip() if view_count else '',
                    'duration': duration.strip() if duration else '',
                    'page': 1
                }
            
        except Exception as e:
            logger.error(f"提取视频信息时出错: {e}")
        
        return None
    
    def collect_all_videos(self, uid: str, max_pages: int = 10) -> List[Dict]:
        """收集用户所有视频"""
        all_videos = []
        
        try:
            self._setup_driver()
            
            # 构建UP主主页URL
            space_url = f"https://space.bilibili.com/{uid}/video"
            logger.info(f"开始收集UID {uid} 的视频...")
            
            # 访问主页
            self.driver.get(space_url)
            self._random_delay(5, 8)
            
            # 等待页面加载
            try:
                WebDriverWait(self.driver, self.wait_time).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".video-list, .bili-video-card"))
                )
            except TimeoutException:
                logger.error("页面加载超时，可能被反爬虫检测")
                return all_videos
            
            # 收集第一页视频
            videos = self.collect_videos_from_page(space_url)
            all_videos.extend(videos)
            
            # 尝试翻页收集更多视频
            page = 2
            while page <= max_pages and len(all_videos) < 1000:  # 限制最大视频数
                try:
                    # 查找下一页按钮
                    next_page_selectors = [
                        ".pagination .next",
                        ".pagination-btn-next",
                        "[aria-label='下一页']",
                        ".next-page"
                    ]
                    
                    next_button = None
                    for selector in next_page_selectors:
                        try:
                            next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if next_button and next_button.is_enabled():
                                break
                        except:
                            continue
                    
                    if not next_button or not next_button.is_enabled():
                        logger.info("没有更多页面了")
                        break
                    
                    # 点击下一页
                    logger.info(f"正在访问第 {page} 页...")
                    self.driver.execute_script("arguments[0].click();", next_button)
                    self._random_delay(4, 7)
                    
                    # 等待新页面加载
                    time.sleep(3)
                    
                    # 收集当前页视频
                    videos = self.collect_videos_from_page(self.driver.current_url)
                    for video in videos:
                        video['page'] = page
                    all_videos.extend(videos)
                    
                    page += 1
                    
                except Exception as e:
                    logger.error(f"翻页失败: {e}")
                    break
            
            logger.info(f"共收集到 {len(all_videos)} 个视频")
            
        except Exception as e:
            logger.error(f"收集视频时出错: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("浏览器已关闭")
        
        return all_videos
    
    def save_to_csv(self, videos: List[Dict], filename: str):
        """保存视频信息到CSV文件"""
        if not videos:
            logger.warning("没有视频数据可保存")
            return
            
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['bvid', 'title', 'video_url', 'view_count', 'duration', 'page']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(videos)
                
            logger.info(f"视频信息已保存到 {filename}")
            
        except Exception as e:
            logger.error(f"保存CSV文件时出错: {e}")
    
    def collect_from_url(self, up_url: str) -> List[Dict]:
        """从UP主主页URL收集所有视频"""
        uid = self.get_uid_from_url(up_url)
        if not uid:
            logger.error("无法从URL中提取UID")
            return []
        
        videos = self.collect_all_videos(uid)
        
        if videos:
            filename = f"bilibili_selenium_videos_{uid}.csv"
            self.save_to_csv(videos, filename)
        
        return videos

def main():
    """主函数"""
    print("=" * 50)
    print("B站视频收集器 - Selenium版本")
    print("=" * 50)
    print("⚠️  注意：此版本需要安装Chrome浏览器和ChromeDriver")
    print("📦 安装依赖：pip install selenium")
    print("=" * 50)
    
    # 询问是否使用无头模式
    headless_input = input("是否使用无头模式？(y/n，默认n): ").strip().lower()
    headless = headless_input == 'y'
    
    # 询问是否使用代理
    proxy = input("代理服务器地址 (可选，格式: ip:port): ").strip()
    proxy = proxy if proxy else None
    
    collector = BilibiliSeleniumCollector(headless=headless, proxy=proxy)
    
    while True:
        print("\n请选择操作:")
        print("1. 输入UP主主页URL收集视频")
        print("2. 输入UID直接收集视频")
        print("3. 退出")
        
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == '1':
            up_url = input("请输入UP主主页URL: ").strip()
            if up_url:
                videos = collector.collect_from_url(up_url)
                if videos:
                    print(f"\n✅ 成功收集到 {len(videos)} 个视频!")
                    print("📁 文件已保存到当前目录")
                else:
                    print("❌ 收集失败，请检查URL是否正确")
        
        elif choice == '2':
            uid = input("请输入UP主UID: ").strip()
            if uid and uid.isdigit():
                videos = collector.collect_all_videos(uid)
                if videos:
                    filename = f"bilibili_selenium_videos_{uid}.csv"
                    collector.save_to_csv(videos, filename)
                    print(f"\n✅ 成功收集到 {len(videos)} 个视频!")
                    print(f"📁 文件已保存到: {filename}")
                else:
                    print("❌ 收集失败，请检查UID是否正确")
            else:
                print("❌ 请输入有效的UID")
        
        elif choice == '3':
            print("👋 再见!")
            break
        
        else:
            print("❌ 无效选择，请重新输入")

if __name__ == "__main__":
    main() 