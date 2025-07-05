import os
import subprocess
import time
import logging
from typing import Optional
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YouTubeDLDownloader:
    """使用youtube-dl的YouTube下载器"""
    
    def __init__(self):
        """初始化下载器"""
        self.check_youtube_dl()
    
    def check_youtube_dl(self):
        """检查youtube-dl是否可用"""
        try:
            result = subprocess.run(['youtube-dl', '--version'], 
                                  capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                logger.info(f"youtube-dl版本: {result.stdout.strip()}")
                return True
            else:
                logger.error("youtube-dl未正确安装")
                return False
        except FileNotFoundError:
            logger.error("youtube-dl未找到，请安装: pip install youtube-dl")
            return False
    
    def download_audio(self, url: str, output_file: Optional[str] = None) -> Optional[str]:
        """
        下载YouTube视频的音频
        
        Args:
            url: YouTube视频URL
            output_file: 输出文件名，如果为None则自动生成
            
        Returns:
            下载成功的音频文件路径，失败返回None
        """
        try:
            if output_file is None:
                video_id = self._extract_video_id(url)
                output_file = f"audio_{video_id}.mp4"
            
            # 检查是否已存在同名文件，如果存在则删除
            if os.path.exists(output_file):
                os.remove(output_file)
                logger.info(f"删除已存在的文件: {output_file}")
            
            # 构建youtube-dl命令
            cmd = [
                'youtube-dl',
                '--extract-audio',
                '--audio-format', 'mp4',
                '--audio-quality', '0',
                '--output', output_file,
                '--no-check-certificate',
                '--ignore-errors',
                '--no-warnings',
                '--quiet',
                url
            ]
            
            logger.info(f"正在下载音频: {url}")
            logger.info(f"输出文件: {output_file}")
            logger.info(f"执行命令: {' '.join(cmd)}")
            
            # 执行下载命令
            result = subprocess.run(cmd, capture_output=True, shell=True)
            
            # 检查下载结果
            if result.returncode == 0:
                if os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    if file_size > 0:
                        logger.info(f"音频下载成功: {output_file} (大小: {file_size} 字节)")
                        return output_file
                    else:
                        logger.error(f"下载的文件大小为0: {output_file}")
                        return None
                else:
                    logger.error(f"下载完成但文件不存在: {output_file}")
                    return None
            else:
                stderr_text = result.stderr.decode('utf-8', errors='ignore') if result.stderr else ""
                stdout_text = result.stdout.decode('utf-8', errors='ignore') if result.stdout else ""
                logger.error(f"音频下载失败，返回码: {result.returncode}")
                logger.error(f"错误信息: {stderr_text}")
                logger.error(f"标准输出: {stdout_text}")
                
                # 提供详细的错误解决方案
                self._handle_download_error(stderr_text)
                return None
                
        except FileNotFoundError:
            logger.error("youtube-dl 未找到，请确保已安装 youtube-dl: pip install youtube-dl")
            return None
        except Exception as e:
            logger.error(f"下载音频时出错: {e}")
            return None
    
    def download_video(self, url: str, output_file: Optional[str] = None) -> Optional[str]:
        """
        下载YouTube视频（包含视频和音频）
        
        Args:
            url: YouTube视频URL
            output_file: 输出文件名，如果为None则自动生成
            
        Returns:
            下载成功的视频文件路径，失败返回None
        """
        try:
            if output_file is None:
                video_id = self._extract_video_id(url)
                output_file = f"video_{video_id}.mp4"
            
            # 检查是否已存在同名文件，如果存在则删除
            if os.path.exists(output_file):
                os.remove(output_file)
                logger.info(f"删除已存在的文件: {output_file}")
            
            # 构建youtube-dl命令
            cmd = [
                'youtube-dl',
                '--format', 'best[ext=mp4]/best',
                '--output', output_file,
                '--no-check-certificate',
                '--ignore-errors',
                '--no-warnings',
                '--quiet',
                url
            ]
            
            logger.info(f"正在下载视频: {url}")
            logger.info(f"输出文件: {output_file}")
            logger.info(f"执行命令: {' '.join(cmd)}")
            
            # 执行下载命令
            result = subprocess.run(cmd, capture_output=True, shell=True)
            
            # 检查下载结果
            if result.returncode == 0:
                if os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    if file_size > 0:
                        logger.info(f"视频下载成功: {output_file} (大小: {file_size} 字节)")
                        return output_file
                    else:
                        logger.error(f"下载的文件大小为0: {output_file}")
                        return None
                else:
                    logger.error(f"下载完成但文件不存在: {output_file}")
                    return None
            else:
                stderr_text = result.stderr.decode('utf-8', errors='ignore') if result.stderr else ""
                stdout_text = result.stdout.decode('utf-8', errors='ignore') if result.stdout else ""
                logger.error(f"视频下载失败，返回码: {result.returncode}")
                logger.error(f"错误信息: {stderr_text}")
                logger.error(f"标准输出: {stdout_text}")
                return None
                
        except FileNotFoundError:
            logger.error("youtube-dl 未找到，请确保已安装 youtube-dl: pip install youtube-dl")
            return None
        except Exception as e:
            logger.error(f"下载视频时出错: {e}")
            return None
    
    def _extract_video_id(self, url: str) -> str:
        """从YouTube URL中提取视频ID"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/watch\?.*v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # 如果没有匹配到，返回时间戳作为ID
        return f"video_{int(time.time())}"
    
    def _handle_download_error(self, error_msg: str):
        """处理下载错误并提供解决方案"""
        if "Sign in to confirm you're not a bot" in error_msg:
            logger.error("检测到YouTube认证问题，请尝试以下解决方案：")
            logger.error("1. 使用 --cookies 参数指定cookies文件")
            logger.error("2. 使用代理服务器")
            logger.error("3. 等待一段时间后重试")
        elif "Video unavailable" in error_msg:
            logger.error("视频不可用，可能原因：")
            logger.error("1. 视频已被删除或设为私有")
            logger.error("2. 地区限制")
            logger.error("3. 年龄限制")
        elif "This video is not available" in error_msg:
            logger.error("视频不可用，请检查URL是否正确")
        else:
            logger.error("未知错误，请检查网络连接和youtube-dl版本")

def test_youtube_dl_download():
    """测试youtube-dl下载功能"""
    print("=== 测试youtube-dl下载功能 ===")
    
    downloader = YouTubeDLDownloader()
    
    # 测试URL
    test_url = "https://www.youtube.com/watch?v=8j1fS_kNIBc&t=3718s"
    
    print(f"测试URL: {test_url}")
    
    # 测试音频下载
    print("\n1. 测试音频下载...")
    audio_file = downloader.download_audio(test_url, "test_audio.mp4")
    
    if audio_file and os.path.exists(audio_file):
        file_size = os.path.getsize(audio_file)
        print(f"✅ 音频下载成功！文件大小: {file_size} 字节")
        audio_success = True
    else:
        print("❌ 音频下载失败！")
        audio_success = False
    
    # 测试视频下载
    print("\n2. 测试视频下载...")
    video_file = downloader.download_video(test_url, "test_video.mp4")
    
    if video_file and os.path.exists(video_file):
        file_size = os.path.getsize(video_file)
        print(f"✅ 视频下载成功！文件大小: {file_size} 字节")
        video_success = True
    else:
        print("❌ 视频下载失败！")
        video_success = False
    
    return audio_success, video_success

if __name__ == "__main__":
    audio_success, video_success = test_youtube_dl_download()
    
    if audio_success or video_success:
        print("\n🎉 部分或全部下载成功！")
        if audio_success:
            print("- 音频下载功能正常")
        if video_success:
            print("- 视频下载功能正常")
    else:
        print("\n💥 所有下载都失败了！")
        