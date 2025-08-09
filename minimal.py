# minimal_test.py - 最简测试
import requests
import json

def test_single_endpoint():
    """测试单个端点"""
    url = "http://localhost:8000/api/v1/questionnaire/questions"
    
    print(f"🔍 测试URL: {url}")
    
    try:
        # 添加详细的请求头
        headers = {
            'User-Agent': 'Python-Test-Client/1.0',
            'Accept': 'application/json',
            'Connection': 'close'
        }
        
        print("📤 发送请求...")
        # 禁用代理
        proxies = {
            'http': None,
            'https': None
        }
        
        response = requests.get(url, headers=headers, timeout=30, proxies=proxies)
        
        print(f"📥 状态码: {response.status_code}")
        print(f"📋 响应头: {dict(response.headers)}")
        print(f"📄 响应长度: {len(response.content)} bytes")
        
        if response.text:
            print(f"📝 响应内容前200字符: {response.text[:200]}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ JSON解析成功")
                    if 'data' in data and 'questions' in data['data']:
                        questions = data['data']['questions']
                        print(f"🎯 获取到 {len(questions)} 个问题")
                    else:
                        print(f"⚠️ 响应格式异常: {data}")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失败: {e}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
        else:
            print("❌ 空响应")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接错误: {e}")
    except requests.exceptions.Timeout as e:
        print(f"❌ 超时错误: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

if __name__ == "__main__":
    print("🚀 最简API测试")
    print("=" * 40)
    test_single_endpoint()
    print("=" * 40)