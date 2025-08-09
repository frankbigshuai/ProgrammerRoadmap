# debug_test.py
"""
调试测试脚本 - 检查API连接和响应
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def check_server_status():
    """检查服务器状态"""
    print("🔍 检查服务器状态...")
    
    try:
        # 1. 检查基本连接
        print(f"1️⃣ 测试基本连接: {BASE_URL}")
        response = requests.get(BASE_URL, timeout=5)
        print(f"   状态码: {response.status_code}")
        print(f"   响应内容: {response.text[:200]}")
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败！请检查:")
        print("   1. Flask应用是否正在运行？(python run.py)")
        print("   2. 端口是否正确？(默认8000)")
        print("   3. 防火墙是否阻止连接？")
        return False
    except requests.exceptions.Timeout:
        print("❌ 连接超时！服务器响应太慢")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False
    
    return True

def check_health_endpoint():
    """检查健康检查端点"""
    print("\n2️⃣ 检查健康检查端点...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"   服务状态: {health_data.get('status')}")
            print(f"   数据库状态: {health_data.get('database')}")
            return True
        else:
            print(f"   健康检查失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 健康检查失败: {e}")
        return False

def test_api_endpoints():
    """测试API端点"""
    print("\n3️⃣ 测试API端点...")
    
    endpoints_to_test = [
        "/api/v1/recommendations/learning-paths",
        "/api/v1/questionnaire/questions",
        "/api/v1/questionnaire/categories"
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n   测试: {endpoint}")
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ JSON响应正常")
                    if 'success' in data:
                        print(f"   成功状态: {data['success']}")
                    if 'message' in data:
                        print(f"   消息: {data['message']}")
                except:
                    print(f"   ⚠️ 响应不是有效JSON: {response.text[:100]}")
            else:
                print(f"   ❌ HTTP错误: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")

def check_imports():
    """检查关键模块导入"""
    print("\n4️⃣ 检查关键模块导入...")
    
    try:
        print("   检查Flask应用创建...")
        import sys
        import os
        
        # 添加项目路径
        project_root = os.path.dirname(os.path.abspath(__file__))
        if project_root not in sys.path:
            sys.path.append(project_root)
        
        from app import create_app
        print("   ✅ Flask应用模块导入成功")
        
        from app.models.user import User
        print("   ✅ User模型导入成功")
        
        from app.models.question import Question
        print("   ✅ Question模型导入成功")
        
        from app.models.response import Response
        print("   ✅ Response模型导入成功")
        
        try:
            from app.services.recommendation_engine import RecommendationEngine
            print("   ✅ RecommendationEngine导入成功")
        except ImportError as e:
            print(f"   ❌ RecommendationEngine导入失败: {e}")
            print("   请检查 app/services/recommendation_engine.py 是否存在")
            return False
        
        try:
            from app.routes.recommendations import recommendations_bp
            print("   ✅ 推荐路由导入成功")
        except ImportError as e:
            print(f"   ❌ 推荐路由导入失败: {e}")
            print("   请检查 app/routes/recommendations.py 是否存在")
            return False
            
        return True
        
    except Exception as e:
        print(f"   ❌ 模块导入失败: {e}")
        return False

def test_app_creation():
    """测试应用创建"""
    print("\n5️⃣ 测试Flask应用创建...")
    
    try:
        import sys
        import os
        
        project_root = os.path.dirname(os.path.abspath(__file__))
        if project_root not in sys.path:
            sys.path.append(project_root)
        
        from app import create_app
        
        print("   创建Flask应用...")
        app = create_app()
        print("   ✅ Flask应用创建成功")
        
        with app.app_context():
            print("   ✅ 应用上下文正常")
            
            # 测试数据库连接
            try:
                from app.utils.database import check_connection
                if check_connection():
                    print("   ✅ 数据库连接正常")
                else:
                    print("   ❌ 数据库连接失败")
                    return False
            except Exception as e:
                print(f"   ❌ 数据库检查失败: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ 应用创建失败: {e}")
        return False

def main():
    """主诊断函数"""
    print("🩺 ProgrammerRoadmap API 诊断工具")
    print("=" * 50)
    
    # 检查步骤
    steps = [
        ("检查模块导入", check_imports),
        ("测试应用创建", test_app_creation),
        ("检查服务器连接", check_server_status),
        ("检查健康端点", check_health_endpoint),
        ("测试API端点", test_api_endpoints)
    ]
    
    for step_name, step_func in steps:
        print(f"\n🔍 {step_name}...")
        try:
            result = step_func()
            if result is False:
                print(f"\n❌ {step_name} 失败，停止后续检查")
                break
        except Exception as e:
            print(f"\n❌ {step_name} 异常: {e}")
            break
    
    print(f"\n📋 诊断建议:")
    print(f"1. 如果导入失败 → 检查文件路径和Python环境")
    print(f"2. 如果应用创建失败 → 检查数据库连接和配置")
    print(f"3. 如果服务器连接失败 → 运行 'python run.py' 启动服务器")
    print(f"4. 如果API端点失败 → 检查路由注册和蓝图配置")

if __name__ == "__main__":
    main()