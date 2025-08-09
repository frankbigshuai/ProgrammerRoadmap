# test_startup.py - 测试应用启动
import sys
import traceback

def test_imports():
    """测试基础导入"""
    print("🔍 测试模块导入...")
    
    try:
        print("  测试Flask...")
        from flask import Flask
        
        print("  测试配置...")
        from config import get_config
        
        print("  测试数据库...")
        from app.utils.database import init_db
        
        print("  测试应用创建...")
        from app import create_app
        
        print("✅ 所有导入成功")
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        traceback.print_exc()
        return False

def test_app_creation():
    """测试应用创建"""
    print("\n🚀 测试应用创建...")
    
    try:
        from app import create_app
        app = create_app()
        
        print("✅ 应用创建成功")
        print(f"  应用名称: {app.name}")
        print(f"  调试模式: {app.debug}")
        
        # 测试基础路由
        with app.test_client() as client:
            print("\n  测试基础端点...")
            
            # 测试根路径
            response = client.get('/')
            print(f"  GET /: {response.status_code}")
            
            # 测试健康检查
            response = client.get('/health')
            print(f"  GET /health: {response.status_code}")
            
            # 测试API端点
            response = client.get('/api/v1/questionnaire/questions')
            print(f"  GET /api/v1/questionnaire/questions: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ 应用创建失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🧪 ProgrammerRoadmap 启动测试")
    print("=" * 40)
    
    # 测试导入
    if not test_imports():
        print("\n❌ 导入测试失败，请检查依赖和文件结构")
        return
    
    # 测试应用创建
    if not test_app_creation():
        print("\n❌ 应用创建失败")
        return
    
    print("\n" + "=" * 40)
    print("🎉 启动测试通过！")
    print("现在可以运行: python run.py")

if __name__ == "__main__":
    main()