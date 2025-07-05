#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站UP主视频链接收集器
功能：收集指定UP主主页内的所有视频链接
作者：AI Assistant
"""

import requests
import json
import time
import re
import random
from urllib.parse import urljoin, urlparse
import csv
import os
from typing import List, Dict, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BilibiliVideoCollector:
    """B站视频链接收集器"""
    
    def __init__(self):
        self.session = requests.Session()
        
        # 多个User-Agent轮换使用
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Referer': 'https://www.bilibili.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        # API基础URL
        self.base_url = "https://api.bilibili.com"
        
        # 请求计数器
        self.request_count = 0
        
    def _rotate_user_agent(self):
        """轮换User-Agent"""
        self.session.headers['User-Agent'] = random.choice(self.user_agents)
        
    def _random_delay(self, min_delay=5, max_delay=15):
        """随机延迟 - 增加基础等待时间"""
        delay = random.uniform(min_delay, max_delay)
        logger.info(f"随机延迟 {delay:.2f} 秒...")
        time.sleep(delay)
        
    def _get_with_retry(self, url: str, params: Optional[Dict] = None, max_retries: int = 5) -> Optional[requests.Response]:
        """带重试机制的GET请求 - 使用更长的等待时间"""
        for attempt in range(max_retries):
            try:
                # 轮换User-Agent
                self._rotate_user_agent()
                
                # 随机延迟 - 每次请求前都延迟
                if self.request_count > 0:
                    self._random_delay(8, 20)  # 增加延迟范围
                else:
                    # 第一次请求也延迟一下
                    time.sleep(random.uniform(3, 8))
                
                response = self.session.get(url, params=params, timeout=30)  # 增加超时时间
                self.request_count += 1
                
                # 检查响应状态
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Too Many Requests
                    # 使用指数退避策略
                    wait_time = min(60 * (2 ** attempt), 600)  # 最大等待10分钟
                    logger.warning(f"请求过于频繁 (429)，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"HTTP错误 {response.status_code}: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"请求异常 (第 {attempt + 1} 次): {e}")
                if attempt < max_retries - 1:
                    # 使用指数退避策略
                    wait_time = min(30 * (2 ** attempt), 300)  # 最大等待5分钟
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    
        return None
    
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
    
    def get_user_info(self, uid: str) -> Optional[Dict]:
        """获取用户信息"""
        try:
            url = f"{self.base_url}/x/space/acc/info"
            params = {'mid': uid}
            
            response = self._get_with_retry(url, params)
            if not response:
                return None
                
            data = response.json()
            if data['code'] == 0:
                return data['data']
            else:
                error_msg = data.get('message', '未知错误')
                logger.error(f"获取用户信息失败: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"获取用户信息时出错: {e}")
            return None
    
    def get_user_videos(self, uid: str, page: int = 1, page_size: int = 30) -> Optional[Dict]:
        """获取用户视频列表"""
        try:
            url = f"{self.base_url}/x/space/arc/search"
            params = {
                'mid': uid,
                'pn': page,
                'ps': page_size,
                'jsonp': 'jsonp'
            }
            
            response = self._get_with_retry(url, params)
            if not response:
                return None
                
            data = response.json()
            if data['code'] == 0:
                return data['data']
            else:
                error_msg = data.get('message', '未知错误')
                logger.error(f"获取视频列表失败: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"获取视频列表时出错: {e}")
            return None
    
    def collect_all_videos(self, uid: str, max_pages: int = 100) -> List[Dict]:
        """收集用户所有视频信息"""
        all_videos = []
        page = 1
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        logger.info(f"开始收集UID {uid} 的视频...")
        
        while page <= max_pages:
            logger.info(f"正在获取第 {page} 页视频...")
            
            data = self.get_user_videos(uid, page)
            if not data:
                consecutive_errors += 1
                logger.warning(f"第 {page} 页获取失败，连续失败次数: {consecutive_errors}")
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"连续失败 {max_consecutive_errors} 次，停止收集")
                    break
                    
                # 使用指数退避策略等待更长时间
                wait_time = min(60 * (2 ** consecutive_errors), 300)  # 最大等待10分钟
                logger.info(f"等待 {wait_time} 秒后继续...")
                time.sleep(wait_time)
                continue
            else:
                consecutive_errors = 0  # 重置错误计数
                
            videos = data.get('list', {}).get('vlist', [])
            if not videos:
                logger.info("没有更多视频了")
                break
                
            for video in videos:
                video_info = {
                    'bvid': video.get('bvid', ''),
                    'aid': video.get('aid', ''),
                    'title': video.get('title', ''),
                    'description': video.get('description', ''),
                    'duration': video.get('duration', ''),
                    'view': video.get('play', 0),
                    'danmaku': video.get('video_review', 0),
                    'reply': video.get('comment', 0),
                    'favorite': video.get('favorites', 0),
                    'coin': video.get('coins', 0),
                    'share': video.get('share', 0),
                    'like': video.get('like', 0),
                    'created': video.get('created', 0),
                    'pic': video.get('pic', ''),
                    'video_url': f"https://www.bilibili.com/video/{video.get('bvid', '')}",
                    'page': page
                }
                all_videos.append(video_info)
            
            logger.info(f"第 {page} 页收集到 {len(videos)} 个视频")
            
            # 检查是否还有更多页
            if len(videos) < 30:  # 每页默认30个视频
                logger.info("已到达最后一页")
                break
                
            page += 1
        
        logger.info(f"共收集到 {len(all_videos)} 个视频")
        return all_videos
    
    def save_to_csv(self, videos: List[Dict], filename: str):
        """保存视频信息到CSV文件"""
        if not videos:
            logger.warning("没有视频数据可保存")
            return
            
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = [
                    'bvid', 'aid', 'title', 'description', 'duration', 
                    'view', 'danmaku', 'reply', 'favorite', 'coin', 
                    'share', 'like', 'created', 'pic', 'video_url', 'page'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(videos)
                
            logger.info(f"视频信息已保存到 {filename}")
            
        except Exception as e:
            logger.error(f"保存CSV文件时出错: {e}")
    
    def save_urls_only(self, videos: List[Dict], filename: str):
        """只保存视频链接到文本文件"""
        if not videos:
            logger.warning("没有视频数据可保存")
            return
            
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for video in videos:
                    f.write(f"{video['video_url']}\n")
                    
            logger.info(f"视频链接已保存到 {filename}")
            
        except Exception as e:
            logger.error(f"保存链接文件时出错: {e}")
    
    def collect_from_url(self, up_url: str, save_csv: bool = True, save_urls: bool = True) -> List[Dict]:
        """从UP主主页URL收集所有视频"""
        # 提取UID
        uid = self.get_uid_from_url(up_url)
        if not uid:
            logger.error("无法从URL中提取UID")
            return []
        
        # 获取用户信息
        user_info = self.get_user_info(uid)
        if user_info:
            logger.info(f"UP主: {user_info.get('name', 'Unknown')}")
        
        # 收集所有视频
        videos = self.collect_all_videos(uid)
        
        if videos:
            # 生成文件名
            base_filename = f"bilibili_videos_{uid}"
            
            if save_csv:
                csv_filename = f"{base_filename}.csv"
                self.save_to_csv(videos, csv_filename)
            
            if save_urls:
                urls_filename = f"{base_filename}_urls.txt"
                self.save_urls_only(videos, urls_filename)
        
        return videos

def main():
    """主函数"""
    print("=" * 50)
    print("B站UP主视频链接收集器")
    print("=" * 50)
    
    collector = BilibiliVideoCollector()
    
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
                    base_filename = f"bilibili_videos_{uid}"
                    collector.save_to_csv(videos, f"{base_filename}.csv")
                    collector.save_urls_only(videos, f"{base_filename}_urls.txt")
                    print(f"\n✅ 成功收集到 {len(videos)} 个视频!")
                    print("📁 文件已保存到当前目录")
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