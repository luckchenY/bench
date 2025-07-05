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
from selenium.common.exceptions import TimeoutException
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BilibiliSeleniumCollector:
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        
    def _setup_driver(self):
        """设置Chrome浏览器驱动"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # 反检测参数
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 设置用户代理
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        chrome_options.add_argument(f"--user-agent={user_agent}")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
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
    
    def collect_videos(self, uid: str, max_pages=5) -> List[Dict]:
        """收集用户视频"""
        all_videos = []
        
        try:
            self._setup_driver()
            
            # 访问UP主主页
            space_url = f"https://space.bilibili.com/{uid}/video"
            logger.info(f"访问页面: {space_url}")
            
            self.driver.get(space_url)
            self._random_delay(3, 6)
            
            # 等待页面加载
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".video-list, .bili-video-card"))
                )
            except TimeoutException:
                logger.error("页面加载超时")
                return all_videos
            
            # 收集视频
            page = 1
            while page <= max_pages:
                logger.info(f"正在收集第 {page} 页视频...")
                
                # 查找视频元素
                video_elements = self.driver.find_elements(By.CSS_SELECTOR, ".bili-video-card, .video-item")
                
                if not video_elements:
                    logger.info("未找到视频元素")
                    break
                
                # 提取视频信息
                for element in video_elements:
                    try:
                        video_info = self._extract_video_info(element)
                        if video_info:
                            video_info['page'] = page
                            all_videos.append(video_info)
                    except Exception as e:
                        logger.error(f"提取视频信息失败: {e}")
                        continue
                
                logger.info(f"第 {page} 页收集到 {len(video_elements)} 个视频")
                
                # 尝试翻页
                if page < max_pages:
                    try:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, ".pagination .next, .next-page")
                        if next_button and next_button.is_enabled():
                            self.driver.execute_script("arguments[0].click();", next_button)
                            self._random_delay(3, 5)
                            page += 1
                        else:
                            logger.info("没有更多页面了")
                            break
                    except:
                        logger.info("无法找到下一页按钮")
                        break
                else:
                    break
            
        except Exception as e:
            logger.error(f"收集视频时出错: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("浏览器已关闭")
        
        return all_videos
    
    def _extract_video_info(self, element) -> Optional[Dict]:
        """从视频元素中提取信息"""
        try:
            # 提取标题
            title = ""
            try:
                title_elem = element.find_element(By.CSS_SELECTOR, ".title, .bili-video-card__info--tit")
                title = title_elem.get_attribute("title") or title_elem.text
            except:
                pass
            
            # 提取链接
            video_url = ""
            bvid = ""
            try:
                link_elem = element.find_element(By.CSS_SELECTOR, "a[href*='/video/']")
                video_url = link_elem.get_attribute("href")
                if video_url:
                    bvid_match = re.search(r'/video/(BV\w+)', video_url)
                    if bvid_match:
                        bvid = bvid_match.group(1)
            except:
                pass
            
            if title and video_url:
                return {
                    'bvid': bvid,
                    'title': title.strip(),
                    'video_url': video_url
                }
            
        except Exception as e:
            logger.error(f"提取视频信息时出错: {e}")
        
        return None
    
    def save_to_csv(self, videos: List[Dict], filename: str):
        """保存到CSV文件"""
        if not videos:
            return
            
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['bvid', 'title', 'video_url', 'page']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(videos)
                
            logger.info(f"视频信息已保存到 {filename}")
            
        except Exception as e:
            logger.error(f"保存CSV文件时出错: {e}")

def main():
    print("=" * 50)
    print("B站视频收集器 - Selenium版本")
    print("=" * 50)
    
    headless = input("是否使用无头模式？(y/n，默认n): ").strip().lower() == 'y'
    
    collector = BilibiliSeleniumCollector(headless=headless)
    
    uid = input("请输入UP主UID: ").strip()
    if uid and uid.isdigit():
        videos = collector.collect_videos(uid, max_pages=3)
        if videos:
            filename = f"bilibili_selenium_videos_{uid}.csv"
            collector.save_to_csv(videos, filename)
            print(f"\n✅ 成功收集到 {len(videos)} 个视频!")
            print(f"📁 文件已保存到: {filename}")
        else:
            print("❌ 收集失败")
    else:
        print("❌ 请输入有效的UID")

if __name__ == "__main__":
    main() 