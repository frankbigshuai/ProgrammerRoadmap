# quick_test.py - 快速API测试
#ok
import requests
import json
import time
import flask

BASE_URL = "http://localhost:8000"

def test_basic_endpoints():
    """测试基础端点"""
    print("🔍 测试基础端点（无需认证）")
    
    # 1. 获取问题列表
    print("\n1. 获取问题列表...")
    try:
        # 禁用代理
        proxies = {'http': None, 'https': None}
        response = requests.get(f"{BASE_URL}/api/v1/questionnaire/questions", timeout=30, proxies=proxies)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            questions = data['data']['questions']
            print(f"✅ 获取到 {len(questions)} 个问题")
            
            # 显示问题概览
            print("问题概览:")
            for q in questions[:3]:  # 只显示前3个
                print(f"  - {q['question_id']}: {q['question_text']}")
        else:
            print(f"❌ 获取问题失败: {response.status_code}")
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 2. 获取问题分类
    print("\n2. 获取问题分类...")
    try:
        proxies = {'http': None, 'https': None}
        response = requests.get(f"{BASE_URL}/api/v1/questionnaire/categories", timeout=30, proxies=proxies)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            categories = data['data']['categories']
            print(f"✅ 获取到 {len(categories)} 个分类")
            for cat in categories:
                print(f"  - {cat['category']}: {cat['name']} ({cat['question_count']} 个问题)")
        else:
            print(f"❌ 获取分类失败: {response.status_code}")
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 3. 获取学习路径
    print("\n3. 获取学习路径...")
    try:
        proxies = {'http': None, 'https': None}
        response = requests.get(f"{BASE_URL}/api/v1/recommendations/learning-paths", timeout=30, proxies=proxies)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            paths = data['data']['paths']
            print(f"✅ 获取到 {len(paths)} 个学习路径")
            for path_name, path_info in paths.items():
                print(f"  - {path_name}: {path_info['name']} ({path_info['duration_weeks']} 周)")
        else:
            print(f"❌ 获取路径失败: {response.status_code}")
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def test_user_registration():
    """测试用户注册"""
    print("\n🔐 测试用户注册")
    
    timestamp = int(time.time())
    user_data = {
        "username": f"testuser_{timestamp}",
        "email": f"test_{timestamp}@example.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        if response.status_code == 201:
            data = response.json()
            print(f"✅ 用户注册成功: {data['data']['username']}")
            return data['data']['token']
        else:
            print(f"❌ 注册失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 注册请求失败: {e}")
        return None

def test_authenticated_endpoints(token):
    """测试需要认证的端点"""
    print("\n🔒 测试认证端点")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. 获取用户资料
    print("\n1. 获取用户资料...")
    try:
        response = requests.get(f"{BASE_URL}/auth/profile", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 获取资料成功: {data['data']['username']}")
        else:
            print(f"❌ 获取资料失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 2. 提交答案
    print("\n2. 提交测试答案...")
    test_answers = [
        {"question_id": "skill_001", "answer_value": "intermediate"},
        {"question_id": "interest_001", "answer_value": "web_frontend"},
        {"question_id": "goal_001", "answer_value": "skill_upgrade"}
    ]
    
    for answer in test_answers:
        try:
            response = requests.post(f"{BASE_URL}/responses/submit", json=answer, headers=headers)
            if response.status_code == 200:
                data = response.json()
                progress = data['data']['progress']
                print(f"✅ 答案提交成功: {answer['question_id']} (进度: {progress['progress_percentage']}%)")
            else:
                print(f"❌ 提交失败 {answer['question_id']}: {response.status_code}")
        except Exception as e:
            print(f"❌ 提交请求失败: {e}")
    
    # 3. 生成推荐
    print("\n3. 生成推荐...")
    try:
        response = requests.post(f"{BASE_URL}/recommendations/generate", headers=headers)
        if response.status_code == 200:
            data = response.json()
            recommendation = data['data']['recommendation']
            print(f"✅ 推荐生成成功!")
            print(f"  推荐路径: {recommendation['primary_path']['name']}")
            print(f"  置信度: {data['confidence_score']}")
        else:
            result = response.json()
            print(f"❌ 推荐生成失败: {result.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"❌ 推荐请求失败: {e}")

def main():
    """主测试函数"""
    print("🚀 ProgrammerRoadmap API 快速测试")
    print("=" * 50)
    
    try:
        # 测试基础端点
        test_basic_endpoints()
        
        # 测试用户注册
        token = test_user_registration()
        
        if token:
            # 测试认证端点
            test_authenticated_endpoints(token)
        
        print("\n" + "=" * 50)
        print("🎉 测试完成!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败!")
        print("请确保API服务器正在运行:")
        print("  python run.py")
        print("然后在新终端运行此测试脚本")

if __name__ == "__main__":
    main()