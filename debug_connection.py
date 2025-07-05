# #!/usr/bin/env python3
# import requests
# import json
# import socket
# import ssl

# def test_network():
#     """测试网络连接"""
#     print("=== 网络连接测试 ===")
    
#     # 测试DNS解析
#     try:
#         ip = socket.gethostbyname("dashscope.aliyuncs.com")
#         print(f"✅ DNS解析成功: dashscope.aliyuncs.com -> {ip}")
#     except Exception as e:
#         print(f"❌ DNS解析失败: {e}")
#         return False
    
#     # 测试端口连接
#     try:
#         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         sock.settimeout(10)
#         result = sock.connect_ex(("dashscope.aliyuncs.com", 443))
#         sock.close()
#         if result == 0:
#             print("✅ 端口443连接成功")
#         else:
#             print(f"❌ 端口443连接失败: {result}")
#             return False
#     except Exception as e:
#         print(f"❌ 端口连接测试失败: {e}")
#         return False
    
#     return True

# def test_ssl():
#     """测试SSL连接"""
#     print("\n=== SSL连接测试 ===")
#     try:
#         context = ssl.create_default_context()
#         with socket.create_connection(("dashscope.aliyuncs.com", 443), timeout=10) as sock:
#             with context.wrap_socket(sock, server_hostname="dashscope.aliyuncs.com") as ssock:
#                 print(f"✅ SSL连接成功")
#                 print(f"SSL版本: {ssock.version()}")
#                 return True
#     except Exception as e:
#         print(f"❌ SSL连接失败: {e}")
#         return False

# def test_http_request():
#     """测试HTTP请求"""
#     print("\n=== HTTP请求测试 ===")
    
#     # 测试1: 简单的GET请求
#     try:
#         response = requests.get("https://dashscope.aliyuncs.com", timeout=10)
#         print(f"✅ GET请求成功: {response.status_code}")
#     except Exception as e:
#         print(f"❌ GET请求失败: {e}")
#         return False
    
#     # 测试2: 测试API端点
#     try:
#         response = requests.get("https://dashscope.aliyuncs.com/compatible-mode/v1", timeout=10)
#         print(f"✅ API端点可访问: {response.status_code}")
#     except Exception as e:
#         print(f"❌ API端点访问失败: {e}")
#         return False
    
#     return True

# def test_api_auth():
#     """测试API认证"""
#     print("\n=== API认证测试 ===")
    
#     # api_key = "sk-c53253ae668c46b382b8c6e02a90553b"
#     api_key = "sk-vVpRZhNVQapnOED2oP0aUJyDOwEcYpDZqhx12pV6jwCKYaHl"
#     url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    
#     headers = {
#         'Authorization': f'Bearer {api_key}',
#         'Content-Type': 'application/json'
#     }
    
#     payload = {
#         "model": "qwen-plus",
#         "messages": [
#             {
#                 "role": "user",
#                 "content": "test"
#             }
#         ],
#         "max_tokens": 10
#     }
    
#     try:
#         response = requests.post(url, json=payload, headers=headers, timeout=30)
#         print(f"状态码: {response.status_code}")
#         print(f"响应头: {dict(response.headers)}")
        
#         if response.status_code == 200:
#             print("✅ API认证成功")
#             return True
#         elif response.status_code == 401:
#             print("❌ API密钥无效")
#             return False
#         elif response.status_code == 403:
#             print("❌ API密钥权限不足")
#             return False
#         else:
#             print(f"❌ 其他错误: {response.text}")
#             return False
            
#     except requests.exceptions.Timeout:
#         print("❌ 请求超时")
#         return False
#     except requests.exceptions.ConnectionError:
#         print("❌ 连接错误")
#         return False
#     except Exception as e:
#         print(f"❌ 请求失败: {e}")
#         return False

# def check_proxy():
#     """检查代理设置"""
#     print("\n=== 代理设置检查 ===")
    
#     # 检查环境变量
#     import os
#     http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
#     https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    
#     if http_proxy:
#         print(f"⚠️ 发现HTTP代理: {http_proxy}")
#     if https_proxy:
#         print(f"⚠️ 发现HTTPS代理: {https_proxy}")
    
#     if not http_proxy and not https_proxy:
#         print("✅ 未发现代理设置")
#     else:
#         print("💡 如果连接有问题，请检查代理设置")

# def main():
#     """主函数"""
#     print("千问API连接问题诊断")
#     print("=" * 50)
    
#     # 检查代理
#     check_proxy()
    
#     # 测试网络
#     if not test_network():
#         print("\n❌ 网络连接有问题，请检查网络设置")
#         return
    
#     # 测试SSL
#     if not test_ssl():
#         print("\n❌ SSL连接有问题，可能是证书或防火墙问题")
#         return
    
#     # 测试HTTP
#     if not test_http_request():
#         print("\n❌ HTTP请求有问题")
#         return
    
#     # 测试API认证
#     if not test_api_auth():
#         print("\n❌ API认证有问题，请检查API密钥")
#         return
    
#     print("\n✅ 所有测试通过，连接正常")

# if __name__ == "__main__":
#     main() 


import base64
from openai import OpenAI

client = OpenAI(
    base_url="http://35.220.164.252:3888/v1/",
    api_key="sk-nkzqPzJXQeo3tNUU8mMPSWCAqbO9g7rkpCPrCXFu4lVHmrnB"
)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


image_path = "sys.png"

base64_image = encode_image(image_path)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "这张图片里有什么?请详细描述。"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        }
    ],
    temperature=1 # 自行修改温度等参数
)
print(response)
print(response.choices[0].message.content)
