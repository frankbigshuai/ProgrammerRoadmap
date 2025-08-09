# debug_status.py - 调试问卷状态响应
import requests
import json

BASE_URL = "http://localhost:8000"
PROXIES = {'http': None, 'https': None}

def debug_questionnaire_status():
    """调试问卷状态接口返回的数据结构"""
    
    # 1. 创建测试用户
    timestamp = str(int(time.time()))[-6:]
    user_data = {
        "username": f"debug{timestamp}",
        "email": f"debug{timestamp}@example.com",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", 
                           json=user_data, proxies=PROXIES)
    
    if response.status_code != 201:
        print("❌ 无法创建测试用户")
        return
    
    token = response.json()['data']['token']
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. 提交一些答案
    answer_data = {"question_id": "skill_001", "answer_value": "intermediate"}
    requests.post(f"{BASE_URL}/api/v1/responses/submit", 
                 json=answer_data, headers=headers, proxies=PROXIES)
    
    # 3. 获取问卷状态并打印详细信息
    print("🔍 问卷状态接口响应:")
    response = requests.get(f"{BASE_URL}/api/v1/questionnaire/status", 
                          headers=headers, proxies=PROXIES)
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("完整响应:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # 检查 overall_progress 的字段
        overall = data['data']['overall_progress']
        print(f"\noverall_progress 字段:")
        for key, value in overall.items():
            print(f"  {key}: {value}")
    else:
        print(f"错误: {response.text}")
    
    # 4. 同时获取用户答案作为对比
    print(f"\n🔍 用户答案接口响应:")
    response = requests.get(f"{BASE_URL}/api/v1/responses/my-answers", 
                          headers=headers, proxies=PROXIES)
    
    if response.status_code == 200:
        data = response.json()
        print(f"答案数量: {data['data']['count']}")
    else:
        print(f"错误: {response.text}")

if __name__ == "__main__":
    import time
    debug_questionnaire_status()