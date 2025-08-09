# simple_test.py
"""
简化版API测试脚本，增加错误处理
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def safe_request(method, url, **kwargs):
    """安全的HTTP请求，包含详细错误信息"""
    try:
        response = requests.request(method, url, timeout=10, **kwargs)
        print(f"   请求: {method} {url}")
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                return response, response.json()
            except json.JSONDecodeError:
                print(f"   ⚠️ 响应不是JSON格式")
                print(f"   响应内容: {response.text[:200]}")
                return response, None
        else:
            print(f"   ❌ HTTP错误 {response.status_code}")
            print(f"   错误内容: {response.text[:200]}")
            return response, None
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ 连接错误: 无法连接到服务器")
        print(f"   请确保Flask应用正在运行: python run.py")
        return None, None
    except requests.exceptions.Timeout:
        print(f"   ❌ 请求超时")
        return None, None
    except Exception as e:
        print(f"   ❌ 未知错误: {e}")
        return None, None

def test_basic_endpoints():
    """测试基本端点"""
    print("🧪 测试基本API端点")
    print("=" * 40)
    
    # 1. 测试根路径
    print("\n1️⃣ 测试根路径...")
    response, data = safe_request("GET", f"{BASE_URL}/")
    if data:
        print(f"   ✅ 根路径正常: {data.get('message', 'N/A')}")
    
    # 2. 测试健康检查
    print("\n2️⃣ 测试健康检查...")
    response, data = safe_request("GET", f"{BASE_URL}/health")
    if data:
        print(f"   ✅ 健康检查正常")
        print(f"   服务状态: {data.get('status')}")
        print(f"   数据库状态: {data.get('database')}")
    
    # 3. 测试学习路径API
    print("\n3️⃣ 测试学习路径API...")
    response, data = safe_request("GET", f"{BASE_URL}/api/v1/recommendations/learning-paths")
    if data:
        print(f"   ✅ 学习路径API正常")
        paths = data.get('data', {}).get('paths', {})
        print(f"   可用路径数量: {len(paths)}")
        for path_key in list(paths.keys())[:3]:  # 显示前3个
            print(f"     • {paths[path_key]['name']}")
    
    # 4. 测试问卷分类API
    print("\n4️⃣ 测试问卷分类API...")
    response, data = safe_request("GET", f"{BASE_URL}/api/v1/questionnaire/categories")
    if data:
        print(f"   ✅ 问卷分类API正常")
        categories = data.get('data', {}).get('categories', [])
        print(f"   分类数量: {len(categories)}")
    
    # 5. 测试问卷题目API（不需要认证）
    print("\n5️⃣ 测试问卷题目API...")
    response, data = safe_request("GET", f"{BASE_URL}/api/v1/questionnaire/questions")
    if data:
        print(f"   ✅ 问卷题目API正常")
        questions = data.get('data', {}).get('questions', [])
        print(f"   题目数量: {len(questions)}")
    else:
        print(f"   ⚠️ 可能需要先初始化测试数据")
        
def test_user_registration():
    """测试用户注册"""
    print("\n6️⃣ 测试用户注册...")
    
    register_data = {
        "username": f"test_user_{int(__import__('time').time())}",  # 使用时间戳避免重复
        "email": f"test_{int(__import__('time').time())}@example.com",
        "password": "123456"
    }
    
    response, data = safe_request("POST", f"{BASE_URL}/api/v1/auth/register", json=register_data)
    if data and data.get('success'):
        print(f"   ✅ 用户注册成功")
        print(f"   用户名: {data['data']['username']}")
        print(f"   Token长度: {len(data['data']['token'])}")
        return data['data']['token']
    else:
        print(f"   ❌ 用户注册失败")
        return None

def test_with_auth(token):
    """使用认证token测试需要登录的API"""
    if not token:
        print("\n⚠️ 没有有效token，跳过认证测试")
        return
    
    print("\n7️⃣ 测试需要认证的API...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试获取用户资料
    print("\n   测试获取用户资料...")
    response, data = safe_request("GET", f"{BASE_URL}/api/v1/auth/profile", headers=headers)
    if data and data.get('success'):
        print(f"   ✅ 获取用户资料成功")
        print(f"   用户ID: {data['data']['user_id']}")
    
    # 测试推荐生成（可能会失败，因为没有问卷数据）
    print("\n   测试推荐生成...")
    response, data = safe_request("POST", f"{BASE_URL}/api/v1/recommendations/generate", headers=headers)
    if data:
        if data.get('success'):
            print(f"   ✅ 推荐生成成功")
        else:
            print(f"   ⚠️ 推荐生成失败（预期，因为没有问卷数据）")
            print(f"   错误信息: {data.get('message')}")

def main():
    """主测试函数"""
    print("🚀 ProgrammerRoadmap API 简化测试")
    print("=" * 50)
    
    # 测试基本端点
    test_basic_endpoints()
    
    # 测试用户注册
    token = test_user_registration()
    
    # 测试需要认证的API
    test_with_auth(token)
    
    print(f"\n🎉 基本测试完成！")
    print(f"\n📋 下一步建议:")
    print(f"1. 如果所有API都正常，运行: python scripts/init_test_data.py")
    print(f"2. 然后运行完整测试: python test_recommendation_api.py")
    print(f"3. 如果有问题，请把测试输出发给开发者")

if __name__ == "__main__":
    main()