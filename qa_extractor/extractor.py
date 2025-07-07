import json
import re
import prompts
import base64
from openai import OpenAI

def extract_qa_from_audio_genmini(audio_file):
    """
    输入音频文件路径，调用Genmini大模型，返回问答对列表（list of dict）。
    """
    def encode_audio(audio_path):
        with open(audio_path, "rb") as audio_file:
            return base64.b64encode(audio_file.read()).decode('utf-8')

    client = OpenAI(
        base_url="http://35.220.164.252:3888/v1/",
        api_key="sk-vVpRZhNVQapnOED2oP0aUJyDOwEcYpDZqhx12pV6jwCKYaHl"
    )
    base64_audio = encode_audio(audio_file)
    response = client.chat.completions.create(
        model="gemini-2.0-flash-lite-001",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompts.QA_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:audio/mp3;base64,{base64_audio}"
                        }
                    }
                ]
            }
        ],
        temperature=1
    )
    qa_text = response.choices[0].message.content
    if not qa_text:
        return []
    # 解析问答
    blocks = qa_text.strip().split('Q&A')
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