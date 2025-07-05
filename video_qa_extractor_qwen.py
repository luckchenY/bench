#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站科研视频现场问答提取器
从视频内容中提取分享结束后的现场问答环节
"""

import requests
import json
import time
import csv
import re
import os
import subprocess
from typing import List, Dict, Optional
from datetime import datetime
import logging
import backports.tarfile

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioExtractor:
    """音频提取器"""
    
    def __init__(self):
        pass
    
    def download_bilibili_audio(self, bvid: str, output_file: Optional[str] = None) -> Optional[str]:
        """下载B站视频音频"""
        try:
            if output_file is None:
                output_file = f"audio_{bvid}.wav"
            
            video_url = f"https://www.bilibili.com/video/{bvid}"
            
            # 使用yt-dlp下载音频
            cmd = [
                'yt-dlp',
                '--extract-audio',
                '--audio-format', 'wav',
                '--audio-quality', '0',
                '--output', output_file,
                video_url
            ]
            
            logger.info(f"正在下载音频: {bvid}")
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='gbk', shell=True)
            
            if result.returncode == 0 and os.path.exists(output_file):
                logger.info(f"音频下载成功: {output_file}")
                return output_file
            else:
                logger.error(f"音频下载失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"下载音频时出错: {e}")
            return None
    
    def extract_audio_from_file(self, video_file: str, output_file: Optional[str] = None) -> Optional[str]:
        """从本地视频文件提取音频"""
        try:
            if output_file is None:
                base_name = os.path.splitext(video_file)[0]
                output_file = f"{base_name}_audio.wav"
            
            # 更简单的FFmpeg命令，兼容性更好
            cmd = [
                'ffmpeg',
                '-i', video_file,
                '-vn',  # 不包含视频
                '-acodec', 'pcm_s16le',  # 音频编码
                '-ar', '16000',  # 采样率
                '-ac', '1',  # 单声道
                '-y',  # 覆盖输出文件
                output_file
            ]
            
            logger.info(f"正在提取音频: {video_file}")
            logger.info(f"FFmpeg命令: {' '.join(cmd)}")
            
            # 修复Windows下的编码问题
            if os.name == 'nt':  # Windows
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', shell=True)
            else:  # Unix/Linux
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0 and os.path.exists(output_file):
                logger.info(f"音频提取成功: {output_file}")
                return output_file
            else:
                logger.error(f"音频提取失败，返回码: {result.returncode}")
                logger.error(f"错误信息: {result.stderr}")
                logger.error(f"标准输出: {result.stdout}")
                return None
                
        except FileNotFoundError:
            logger.error("FFmpeg未找到，请确保已安装FFmpeg并添加到PATH")
            return None
        except Exception as e:
            logger.error(f"提取音频时出错: {e}")
            return None

class SpeechRecognizer:
    """语音识别器"""
    
    def __init__(self):
        pass
    
    def transcribe_with_whisper(self, audio_file: str, model_size: str = "base") -> Optional[str]:
        """使用Whisper进行语音识别"""
        try:
            import whisper
            
            # 检查音频文件是否存在
            if not os.path.exists(audio_file):
                logger.error(f"音频文件不存在: {audio_file}")
                return None
            
            logger.info(f"正在使用Whisper {model_size}模型进行语音识别...")
            logger.info(f"音频文件: {audio_file}")
            
            # 添加模型下载重试机制
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    model = whisper.load_model(model_size)
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"模型下载失败，尝试重试 ({attempt + 1}/{max_retries}): {e}")
                        time.sleep(5)  # 等待5秒后重试
                    else:
                        logger.error(f"模型下载最终失败: {e}")
                        return None
            
            # 设置识别参数
            result = model.transcribe(
                audio_file, 
                language="zh",  # 指定中文
                task="transcribe",  # 转录任务
                verbose=True  # 显示进度
            )
            
            transcript = result["text"]
            # Ensure transcript is a string
            if isinstance(transcript, list):
                transcript = " ".join(transcript)
            
            logger.info(f"语音识别完成，转录文本长度: {len(transcript)} 字符")
            
            return transcript
            
        except ImportError:
            logger.error("Whisper未安装，请运行: pip install openai-whisper")
            return None
        except Exception as e:
            logger.error(f"Whisper识别失败: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            return None

class QAExtractor:
    """问答提取器 - 使用千问API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def extract_qa_from_transcript(self, transcript: str, video_title: str) -> List[Dict]:
        """从转录文本中提取问答内容"""
        if not transcript:
            return []
        
        # 构建提示词
        prompt = f"""
你是一个专业的科研视频问答内容分析专家。请分析以下转录文本，专门提取分享结束后的现场问答环节。

视频标题: {video_title}

转录文本:
{transcript}

请按照以下规则识别问答环节：

1. 寻找以下关键词或短语，这些通常标志着问答环节的开始：
   - "大家有没有什么问题"
   - "有什么问题吗"
   - "现在进入问答环节"
   - "请提问"
   - "有问题可以举手"
   - "我们开始提问"
   - "接下来是提问时间"

2. 识别问答模式：
   - 问题通常包含疑问词：什么、怎么、为什么、如何、是否等
   - 回答通常是对问题的直接回应
   - 问答之间有明确的逻辑关系

3. 提取格式：
Q&A对1:
提问者: ["观众"]
问题: [提取完整的问题内容]
回答者: ["分享人"]
回答: [提取完整的回答内容]

Q&A对2:
提问者: ["观众"]
问题: [问题内容]
回答者: ["分享人"]
回答: [回答内容]

要求：
1. 只提取现场问答环节，不包括分享内容
2. 保持问答的原始顺序
3. 如果转录文本不完整或质量不好，请标注
4. 如果找不到明显的问答环节，请说明"未找到问答环节"

请直接返回格式化的问答内容，不要添加其他说明。
"""
        
        try:
            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": "qwen-plus",
                "messages": [
                    {
                        "role": "system", 
                        "content": "你是专业的科研视频问答内容分析专家，专门提取现场问答环节。"
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 4000
            }
            
            response = self.session.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    qa_text = result['choices'][0]['message']['content']
                    return self._parse_qa_result(qa_text)
                else:
                    logger.error("API响应格式异常")
            else:
                logger.error(f"API请求失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"API调用失败: {e}")
        
        return []
    
    def _parse_qa_result(self, qa_text: str) -> List[Dict]:
        """解析问答结果"""
        qa_pairs = []
        
        # 使用正则表达式提取问答对
        qa_pattern = r'Q&A对\d+:\s*提问者:\s*(.*?)\s*问题:\s*(.*?)\s*回答者:\s*(.*?)\s*回答:\s*(.*?)(?=Q&A对|$)'
        matches = re.findall(qa_pattern, qa_text, re.DOTALL)
        
        for i, match in enumerate(matches, 1):
            questioner, question, answerer, answer = match
            qa_pairs.append({
                'qa_id': i,
                'questioner': questioner.strip(),
                'question': question.strip(),
                'answerer': answerer.strip(),
                'answer': answer.strip(),
                'extracted_time': datetime.now().isoformat()
            })
        
        logger.info(f"解析到 {len(qa_pairs)} 个问答对")
        return qa_pairs

class VideoQAProcessor:
    """视频问答处理器"""
    
    def __init__(self, qianwen_api_key: str):
        self.audio_extractor = AudioExtractor()
        self.speech_recognizer = SpeechRecognizer()
        self.qa_extractor = QAExtractor(qianwen_api_key)
    
    def process_bilibili_video(self, video_url: str, video_title: str) -> Dict:
        """处理B站视频"""
        logger.info(f"开始处理B站视频: {video_title}")
        
        # 从URL中提取BVID
        bvid = self._extract_bvid_from_url(video_url)
        if not bvid:
            return {
                'video_url': video_url,
                'title': video_title,
                'status': 'invalid_url',
                'qa_pairs': []
            }
        
        logger.info(f"提取到BVID: {bvid}")
        
        # 1. 下载音频
        logger.info("步骤1: 下载视频音频...")
        audio_file = self.audio_extractor.download_bilibili_audio(bvid)
        if not audio_file:
            return {
                'video_url': video_url,
                'bvid': bvid,
                'title': video_title,
                'status': 'audio_download_failed',
                'qa_pairs': []
            }
        
        # 2. 语音识别
        logger.info("步骤2: 进行语音识别...")
        speech_recognizer = SpeechRecognizer()
        transcript = speech_recognizer.transcribe_with_whisper(audio_file)
        
        # 清理临时音频文件
        try:
            if os.path.exists(audio_file):
                os.remove(audio_file)
                print("临时音频文件已清理")
        except Exception as e:
            print(f"清理临时文件时出错: {e}")
        
        if not transcript:
            return {
                'video_url': video_url,
                'bvid': bvid,
                'title': video_title,
                'status': 'transcription_failed',
                'qa_pairs': []
            }
        
        # 3. 提取问答
        logger.info("步骤3: 提取问答内容...")
        qa_pairs = self.qa_extractor.extract_qa_from_transcript(transcript, video_title)
        
        return {
            'video_url': video_url,
            'bvid': bvid,
            'title': video_title,
            'transcript_length': len(transcript),
            'qa_pairs': qa_pairs,
            'status': 'success' if qa_pairs else 'no_qa_found'
        }
    
    def _extract_bvid_from_url(self, video_url: str) -> Optional[str]:
        """从视频URL中提取BVID"""
        import re
        
        # 匹配B站视频URL中的BVID
        patterns = [
            r'bilibili\.com/video/(BV\w+)',
            r'b23\.tv/(\w+)',  # 短链接需要进一步处理
            r'BV\w+'  # 直接匹配BVID
        ]
        
        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                bvid = match.group(1) if len(match.groups()) > 0 else match.group(0)
                # 如果是短链接，需要获取真实URL
                if 'b23.tv' in video_url:
                    try:
                        response = requests.head(video_url, allow_redirects=True)
                        real_url = response.url
                        bvid_match = re.search(r'BV\w+', real_url)
                        if bvid_match:
                            return bvid_match.group(0)
                    except:
                        pass
                return bvid
        
        return None
    
    def process_transcript_only(self, transcript: str, video_title: str) -> Dict:
        """只处理转录文本"""
        logger.info(f"处理转录文本: {video_title}")
        
        qa_pairs = self.qa_extractor.extract_qa_from_transcript(transcript, video_title)
        
        return {
            'title': video_title,
            'transcript_length': len(transcript),
            'qa_pairs': qa_pairs,
            'status': 'success' if qa_pairs else 'no_qa_found'
        }
    
    def save_results(self, results: List[Dict], output_file: str):
        """保存结果"""
        try:
            # 保存问答对到CSV
            qa_data = []
            for result in results:
                if result['qa_pairs']:
                    for qa in result['qa_pairs']:
                        qa_data.append({
                            'video_title': result.get('title', ''),
                            'bvid': result.get('bvid', ''),
                            'qa_id': qa['qa_id'],
                            'questioner': qa['questioner'],
                            'question': qa['question'],
                            'answerer': qa['answerer'],
                            'answer': qa['answer'],
                            'extracted_time': qa['extracted_time']
                        })
            
            if qa_data:
                with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                    fieldnames = ['video_title', 'bvid', 'qa_id', 'questioner', 'question', 
                                 'answerer', 'answer', 'extracted_time']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(qa_data)
                
                logger.info(f"问答结果已保存到 {output_file}")
                return len(qa_data)
            else:
                logger.warning("没有问答数据可保存")
                return 0
            
        except Exception as e:
            logger.error(f"保存结果时出错: {e}")
            return 0

def main():
    """主函数 - 处理本地MP4文件"""
    print("=" * 60)
    print("B站科研视频现场问答提取器")
    print("=" * 60)
    
    # 使用固定的API密钥
    api_key = "sk-c53253ae668c46b382b8c6e02a90553b"
    processor = VideoQAProcessor(api_key)
    
    # 本地MP4文件路径
    video_file = "test.mp4"  # 请修改为你的MP4文件路径
    video_title = "科研论文分享视频"  # 请修改为视频标题
    
    print(f"处理视频文件: {video_file}")
    print(f"视频标题: {video_title}")
    print("-" * 60)
    
    # 检查文件是否存在
    if not os.path.exists(video_file):
        print(f"❌ 文件不存在: {video_file}")
        return
    
    # 提取音频
    print("步骤1: 提取音频...")
    audio_extractor = AudioExtractor()
    audio_file = audio_extractor.extract_audio_from_file(video_file)
    
    if not audio_file:
        print("❌ 音频提取失败")
        return
    
    # 语音识别
    print("步骤2: 进行语音识别...")
    speech_recognizer = SpeechRecognizer()
    transcript = speech_recognizer.transcribe_with_whisper(audio_file)
    
    # 清理临时音频文件
    try:
        if os.path.exists(audio_file):
            os.remove(audio_file)
            print("临时音频文件已清理")
    except Exception as e:
        print(f"清理临时文件时出错: {e}")
    
    if not transcript:
        print("❌ 语音识别失败")
        return
    
    print(f"转录文本长度: {len(transcript)} 字符")
    
    # 提取问答
    print("步骤3: 提取问答内容...")
    result = processor.process_transcript_only(transcript, video_title)
    
    if result['qa_pairs']:
        print(f"\n✅ 成功提取到 {len(result['qa_pairs'])} 个现场问答!")
        for qa in result['qa_pairs']:
            print(f"\n问答对 {qa['qa_id']}:")
            print(f"提问者: {qa['questioner']}")
            print(f"问题: {qa['question']}")
            print(f"回答者: {qa['answerer']}")
            print(f"回答: {qa['answer']}")
            print("-" * 40)
        
        # 保存结果
        base_name = os.path.splitext(os.path.basename(video_file))[0]
        output_file = f"video_qa_{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        processor.save_results([result], output_file)
        print(f"\n📁 结果已保存到: {output_file}")
    else:
        print("❌ 未提取到现场问答内容")
        print(f"状态: {result['status']}")

if __name__ == "__main__":
    main() 