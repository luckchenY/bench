import csv
import re
import os
import subprocess
import time
from typing import List, Dict, Optional
from datetime import datetime
import logging
import base64
from dashscope import MultiModalConversation
from openai import OpenAI
from urllib3 import response
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

prompt = f"""
1. You are a professional expert in analyzing Q&A sessions from scientific research videos. Please analyze the following audio and specifically extract the Q&A session that occurs after the main presentation.
Look for the following keywords or phrases, which usually indicate the start of the Q&A session:
"Does anyone have any questions?"
"Are there any questions?"
"Now we enter the Q&A session"
"Please ask questions"
"If you have questions, you can raise your hand"
"Let's start the Q&A"
"Next is the question time"
2. For each questioner, if the same person asks multiple follow-up questions on the same topic, and the same respondent answers, please combine all their consecutive exchanges into a single Q&A block. Each Q&A block should correspond to one questioner and one respondent, and should include all the follow-up questions and answers between them on the same topic. Do not mix questions from different people into the same block.
Only extract the live Q&A session, do not include the main presentation content.
Maintain the original order of the Q&A.
If a question is not academically meaningful, do not include it in your output.
Please convert colloquial expressions in the audio into written language, ensuring the generated content is fluent and clearly expressed.
Return the formatted Q&A content in the following format, and do not add any other explanations:
Q&A
question: [A complete question block, summarizing all consecutive questions from the same questioner on the same topic]
answer: [Corresponding answer block, summarizing all consecutive answers from the same respondent to that questioner on the same topic]
Q&A
question: [Next question block from another questioner]
answer: [Next answer block]
...
"""

class AudioExtractor:
    """音频提取器"""
    
    def __init__(self):
        pass
    
    def download_bilibili_audio(self, bvid: str, output_file: Optional[str] = None) -> Optional[str]:
        """下载B站视频音频"""
        try:
            if output_file is None:
                output_file = f"audio_{bvid}.mp3"
            
            video_url = f"https://www.bilibili.com/video/{bvid}"
            
            # 使用yt-dlp下载音频
            cmd = [
                'yt-dlp',
                '--extract-audio',
                '--audio-format', 'mp3',
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
                output_file = f"{base_name}_audio.mp3"
            
            # 更简单的FFmpeg命令，兼容性更好
            cmd = [
                'ffmpeg',
                '-i', video_file,
                '-vn',  # 不包含视频
                '-acodec', 'libmp3lame',  # 音频编码
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

    def download_audio(self, url: str, output_file: Optional[str] = None) -> Optional[str]:
        try:
            if output_file is None:
                output_file = output_file
            else:
                output_file = "tutorialutobe.mp3"
            # 使用yt-dlp下载音频
            cmd = [
                'yt-dlp',
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '0',
                '--output', output_file,
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='gbk', shell=True)
            
            if result.returncode == 0 and os.path.exists("tutorialutobe.mp3"):
                logger.info(f"音频下载成功: {output_file}")
                return output_file
            else:
                logger.error(f"音频下载失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"下载音频时出错: {e}")
            return None

def encode_audio(audio_path):
    with open(audio_path, "rb") as audio_file:
        return base64.b64encode(audio_file.read()).decode('utf-8')

def extract(audio_file):
    client = OpenAI(
    base_url="http://35.220.164.252:3888/v1/",
    api_key="sk-vVpRZhNVQapnOED2oP0aUJyDOwEcYpDZqhx12pV6jwCKYaHl"
    )
    
    base64_audio = encode_audio(audio_file)
    response=client.chat.completions.create(
        model="gemini-2.0-flash-lite-001",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:audio/mp3;base64,{base64_audio}"
                        }
                    }
                ]
            }
        ],
        temperature=1 # 自行修改温度等参数
    )
    return response
        
def parse_qa_from_text(text):
 
    blocks = text.strip().split('Q&A')
    extracted_data = []
    for block in blocks:
        if not block.strip():
            continue
        question_match = re.search(r'question:\s*(.+)', block)
        response_match = re.search(r'answer:\s*(.+)', block)
        if question_match and response_match:
            qa_pair = {
                'question': question_match.group(1).strip(),
                'response': response_match.group(1).strip()
            }
            extracted_data.append(qa_pair)
    return extracted_data

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8-sig') as jsonfile:
        json.dump(data, jsonfile, ensure_ascii=False, indent=2)

# filename="bilibili_videos_604515161_urls.txt"
# try:
#     with open(filename, 'r', encoding='utf-8', newline='') as csvfile:
#         # 创建一个CSV DictReader对象
#         # 它会自动将第一行作为表头（键）
#         reader = csv.reader(csvfile)
        
#         # 逐行读取数据
#         for i,url in enumerate(reader):
#             bvid = url[0].rsplit('/', 1)[-1]
#             audio_extractor = AudioExtractor()
#             audio_file = audio_extractor.download_bilibili_audio(bvid)

#             result = extract(audio_file)
#             print(result.choices[0].message.content)

#             qa_data = parse_qa_from_text(text=result.choices[0].message.content)
#             output_filename="output2/"+bvid+".csv"
#             if qa_data:
#                 save_to_csv(qa_data, output_filename)
#                 print(f"Successfully extracted {len(qa_data)} Q&A pairs to '{output_filename}'.")
#             else:
#                 print("Could not extract any valid Q&A pairs from the input file.")

# except FileNotFoundError:
    # print(f"错误: 文件 '{filename}' 未找到。")

# path="audio"
# for file in path:
#     # 获取目录下的所有文件名和文件夹名
#     all_items = os.listdir(path)
    
#     for item_name in all_items:
#         # 构建完整路径
#         result = extract(os.path.join(path, item_name))
#         print(result.choices[0].message.content)
#         qa_data = parse_qa_from_text(text=result.choices[0].message.content)
#         output_filename="refined_output/"+os.path.splitext(item_name)[0]+".csv"
#         if qa_data:
#             save_to_csv(qa_data, output_filename)
#             print(f"Successfully extracted {len(qa_data)} Q&A pairs to '{output_filename}'.")
#         else:
#             print("Could not extract any valid Q&A pairs from the input file.")
# audio_extractor = AudioExtractor()
# audio_file = audio_extractor.download_audio("https://www.youtube.com/watch?v=8j1fS_kNIBc&t=3718s",output_file="tutorialutobe.mp3")
audio_extractor = AudioExtractor()
audio_file = audio_extractor.extract_audio_from_file("videoplayback.mp4")
result = extract(audio_file)
print(result.choices[0].message.content)

qa_data = parse_qa_from_text(text=result.choices[0].message.content)
output_filename="refine/test"+time.strftime("%Y%m%d%H%M%S")+".json"
if qa_data:
    save_to_json(qa_data, output_filename)
    print(f"Successfully extracted {len(qa_data)} Q&A pairs to '{output_filename}'.")
else:
    print("Could not extract any valid Q&A pairs from the input file.")
