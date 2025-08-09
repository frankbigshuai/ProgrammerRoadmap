# test_all_api_fixed.py
import requests
import json
import time
import sys

# 🔧 修复requests配置
session = requests.Session()
session.trust_env = False  # 忽略环境代理设置
session.proxies = {}  # 明确禁用代理

# API基础URL
BASE_URL = "http://127.0.0.1:8000"  # 使用127.0.0.1替代localhost
API_BASE = f"{BASE_URL}/api/v1"
TIMEOUT = 30  # 增加超时时间

# 测试数据
test_user = {
    "username": f"testuser_{int(time.time())}",
    "email": f"test_{int(time.time())}@example.com",
    "password": "password123"
}

# 全局变量存储token
auth_token = None
user_id = None

def make_request(method, url, **kwargs):
    """统一的请求函数"""
    kwargs.setdefault('timeout', TIMEOUT)
    return session.request(method, url, **kwargs)

def print_test_header(test_name):
    """打印测试标题"""
    print(f"\n{'='*60}")
    print(f"🧪 {test_name}")
    print('='*60)

def print_response(response, expected_status=200):
    """打印响应结果"""
    print(f"Status: {response.status_code}")
    
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        if response.status_code == expected_status:
            print("✅ 测试通过")
            return True, data
        else:
            print(f"❌ 状态码不匹配 (期望: {expected_status})")
            return False, data
    except:
        print(f"Response Text: {response.text}")
        return False, None

def test_health_check():
    """测试健康检查"""
    print_test_header("健康检查")
    
    response = make_request('GET', f"{BASE_URL}/health")
    success, data = print_response(response)
    return success

def test_index_page():
    """测试首页"""
    print_test_header("首页")
    
    response = make_request('GET', BASE_URL)
    success, data = print_response(response)
    return success

def test_user_registration():
    """测试用户注册"""
    print_test_header("用户注册")
    
    print(f"注册用户: {test_user}")
    
    response = make_request(
        'POST',
        f"{API_BASE}/auth/register",
        headers={"Content-Type": "application/json"},
        json=test_user
    )
    
    success, data = print_response(response, 201)
    
    if success and data:
        global auth_token, user_id
        auth_token = data['data']['token']
        user_id = data['data']['user_id']
        print(f"🔑 获取到Token: {auth_token[:50]}...")
        print(f"👤 用户ID: {user_id}")
    
    return success

def test_user_login():
    """测试用户登录"""
    print_test_header("用户登录")
    
    login_data = {
        "login": test_user["username"],
        "password": test_user["password"]
    }
    
    response = make_request(
        'POST',
        f"{API_BASE}/auth/login",
        headers={"Content-Type": "application/json"},
        json=login_data
    )
    
    success, data = print_response(response)
    
    if success and data:
        global auth_token
        auth_token = data['data']['token']
        print(f"🔑 更新Token: {auth_token[:50]}...")
    
    return success

def test_get_questions():
    """测试获取问卷题目"""
    print_test_header("获取问卷题目")
    
    response = make_request('GET', f"{API_BASE}/questionnaire/questions")
    success, data = print_response(response)
    
    if success and data:
        questions = data['data']['questions']
        print(f"📋 获取到 {len(questions)} 个问题")
        for q in questions:
            print(f"   - {q['question_id']}: {q['question_text']}")
    
    return success

def test_submit_answer():
    """测试提交答案"""
    print_test_header("提交答案")
    
    if not auth_token:
        print("❌ 没有有效的认证令牌")
        return False
    
    # 首先获取问题列表
    response = make_request('GET', f"{API_BASE}/questionnaire/questions")
    if response.status_code != 200:
        print("❌ 无法获取问题列表")
        return False
    
    questions = response.json()['data']['questions']
    if not questions:
        print("⚠️  没有可用的问题")
        # 添加示例问题
        add_sample_questions()
        # 重新获取
        response = make_request('GET', f"{API_BASE}/questionnaire/questions")
        questions = response.json()['data']['questions']
    
    if not questions:
        print("❌ 仍然没有问题可用")
        return False
    
    # 提交第一个问题的答案
    question = questions[0]
    if not question.get('options'):
        print("❌ 问题没有选项")
        return False
    
    answer_data = {
        "question_id": question['question_id'],
        "answer_value": question['options'][0]['value']
    }
    
    print(f"提交答案: {answer_data}")
    
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    response = make_request(
        'POST',
        f"{API_BASE}/responses/submit",
        headers=headers,
        json=answer_data
    )
    
    success, data = print_response(response)
    return success

def test_get_my_answers():
    """测试获取我的答案"""
    print_test_header("获取我的答案")
    
    if not auth_token:
        print("❌ 没有有效的认证令牌")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = make_request('GET', f"{API_BASE}/responses/my-answers", headers=headers)
    
    success, data = print_response(response)
    
    if success and data:
        answers = data['data']['responses']
        print(f"📝 用户有 {len(answers)} 个答案")
    
    return success

def add_sample_questions():
    """添加示例问题"""
    print("📋 添加示例问题...")
    
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from flask import Flask
        from config import DevelopmentConfig
        from app.utils.database import init_db
        from app.models.question import Question
        
        app = Flask(__name__)
        app.config.from_object(DevelopmentConfig)
        
        with app.app_context():
            init_db(app)
            
            sample_questions = [
                {
                    "question_id": "q1",
                    "category": "experience",
                    "question_text": "您的编程基础如何？",
                    "type": "single_choice",
                    "options": [
                        {"value": "beginner", "text": "完全没有经验", "score": 1},
                        {"value": "some_basic", "text": "学过一些基础语法", "score": 2},
                        {"value": "can_code", "text": "能写简单程序", "score": 3}
                    ],
                    "weight": 15,
                    "order": 1
                },
                {
                    "question_id": "q2",
                    "category": "interest",
                    "question_text": "您最感兴趣的开发方向是？",
                    "type": "single_choice",
                    "options": [
                        {"value": "web", "text": "网站开发", "score": 1},
                        {"value": "mobile", "text": "手机应用开发", "score": 1},
                        {"value": "ai", "text": "人工智能", "score": 1}
                    ],
                    "weight": 20,
                    "order": 2
                }
            ]
            
            for q in sample_questions:
                result = Question.create(**q)
                if result:
                    print(f"✅ 创建问题: {q['question_id']}")
    except Exception as e:
        print(f"❌ 添加示例问题失败: {e}")

def main():
    """主测试函数"""
    print("🚀 开始完整API测试...")
    print(f"🌍 测试目标: {BASE_URL}")
    
    # 检查API是否运行
    try:
        response = make_request('GET', f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ API服务未运行，请先启动 python run.py")
            return
        print("✅ API服务运行正常")
    except Exception as e:
        print(f"❌ 无法连接到API服务: {e}")
        return
    
    # 核心测试
    tests = [
        ("健康检查", test_health_check),
        ("首页", test_index_page),
        ("用户注册", test_user_registration),
        ("用户登录", test_user_login),
        ("获取问卷", test_get_questions),
        ("提交答案", test_submit_answer),
        ("获取我的答案", test_get_my_answers),
    ]
    
    # 执行测试
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ 测试 {test_name} 出现异常: {e}")
            results.append((test_name, False))
    
    # 测试总结
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n📈 总计: {passed}/{len(results)} 个测试通过")
    
    if passed == len(results):
        print("🎉 所有测试都通过了！API工作完美！")
    else:
        print("⚠️  有部分测试失败，请检查API实现")

if __name__ == "__main__":
    main()