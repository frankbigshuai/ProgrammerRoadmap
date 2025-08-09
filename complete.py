# complete_flow_test.py - 完整API流程测试
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_complete_workflow():
    """测试完整的API工作流程"""
    print("🚀 ProgrammerRoadmap 完整流程测试")
    print("=" * 60)
    
    # 统一的请求配置
    proxies = {'http': None, 'https': None}
    
    # 1. 用户注册
    print("\n1️⃣ 用户注册测试")
    timestamp = int(time.time())
    short_timestamp = str(timestamp)[-6:]  # 只取后6位
    user_data = {
        "username": f"flow{short_timestamp}",  # 格式: flow123456
        "email": f"flow{short_timestamp}@example.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", 
                               json=user_data, proxies=proxies, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 201:
            user_info = response.json()
            token = user_info['data']['token']
            user_id = user_info['data']['user_id']
            print(f"✅ 注册成功: {user_info['data']['username']}")
            print(f"   用户ID: {user_id}")
            print(f"   Token: {token[:30]}...")
        else:
            print(f"❌ 注册失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 注册请求失败: {e}")
        return False
    
    # 2. 获取用户资料
    print("\n2️⃣ 获取用户资料")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/auth/profile", 
                              headers=headers, proxies=proxies)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            profile = response.json()
            print(f"✅ 获取资料成功: {profile['data']['username']}")
        else:
            print(f"❌ 获取资料失败: {response.text}")
    except Exception as e:
        print(f"❌ 资料请求失败: {e}")
    
    # 3. 获取问题列表
    print("\n3️⃣ 获取问题列表")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/questionnaire/questions", 
                              headers=headers, proxies=proxies)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            questions_data = response.json()
            questions = questions_data['data']['questions']
            print(f"✅ 获取到 {len(questions)} 个问题")
            print("前3个问题:")
            for q in questions[:3]:
                print(f"   - {q['question_id']}: {q['question_text']}")
        else:
            print(f"❌ 获取问题失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 问题请求失败: {e}")
        return False
    
    # 4. 提交问卷答案
    print("\n4️⃣ 提交问卷答案")
    sample_answers = [
        {"question_id": "skill_001", "answer_value": "intermediate"},
        {"question_id": "interest_001", "answer_value": "web_frontend"},
        {"question_id": "goal_001", "answer_value": "skill_upgrade"}
    ]
    
    for i, answer in enumerate(sample_answers, 1):
        try:
            response = requests.post(f"{BASE_URL}/api/v1/responses/submit", 
                                   json=answer, headers=headers, proxies=proxies)
            print(f"答案 {i} 状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                progress = result['data']['progress']
                print(f"   ✅ {answer['question_id']} 提交成功 (进度: {progress['progress_percentage']}%)")
            else:
                print(f"   ❌ {answer['question_id']} 提交失败: {response.text}")
        except Exception as e:
            print(f"   ❌ 答案提交请求失败: {e}")
    
    # 5. 获取用户答案
    print("\n5️⃣ 获取用户答案")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/responses/my-answers", 
                              headers=headers, proxies=proxies)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            answers = response.json()
            count = answers['data']['count']
            print(f"✅ 获取到 {count} 个已回答问题")
        else:
            print(f"❌ 获取答案失败: {response.text}")
    except Exception as e:
        print(f"❌ 答案请求失败: {e}")
    
    # 6. 生成推荐
    print("\n6️⃣ 生成个性化推荐")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/recommendations/generate", 
                               headers=headers, proxies=proxies)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            recommendation = response.json()
            data = recommendation['data']
            primary_path = data['recommendation']['primary_path']
            print(f"✅ 推荐生成成功!")
            print(f"   推荐路径: {primary_path['name']}")
            print(f"   学习时长: {primary_path.get('duration_weeks', 'N/A')} 周")
            print(f"   置信度: {data['confidence_score']}")
        else:
            result = response.json()
            print(f"❌ 推荐生成失败: {result.get('message', response.text)}")
    except Exception as e:
        print(f"❌ 推荐请求失败: {e}")
    
    # 7. 获取推荐结果
    print("\n7️⃣ 获取推荐结果")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/recommendations/my-recommendation", 
                              headers=headers, proxies=proxies)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            recommendation = response.json()
            print(f"✅ 获取推荐成功")
        else:
            print(f"❌ 获取推荐失败: {response.text}")
    except Exception as e:
        print(f"❌ 推荐请求失败: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 完整流程测试完成!")
    print(f"🆔 测试用户ID: {user_id}")
    print(f"👤 测试用户名: {user_data['username']}")
    
    return True

if __name__ == "__main__":
    test_complete_workflow()