# diagnose.py - 系统诊断脚本
import sys
import os
import importlib.util

def check_python_path():
    """检查Python路径"""
    print("🐍 Python环境检查")
    print(f"Python版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"Python路径: {sys.path[:3]}...")  # 只显示前3个

def check_project_structure():
    """检查项目结构"""
    print("\n📁 项目结构检查")
    
    required_files = [
        'app/__init__.py',
        'app/models/user.py',
        'app/models/question.py', 
        'app/models/response.py',
        'app/routes/auth.py',
        'app/routes/questionnaire.py',
        'app/routes/responses.py',
        'app/routes/recommendations.py',
        'app/utils/database.py',
        'app/services/recommendation_engine.py',
        'config.py',
        'run.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️ 缺少文件: {len(missing_files)} 个")
        return False
    else:
        print(f"\n✅ 所有必需文件都存在")
        return True

def check_dependencies():
    """检查依赖包"""
    print("\n📦 依赖包检查")
    
    required_packages = [
        'flask',
        'flask_pymongo', 
        'flask_cors',
        'pymongo',
        'jwt',
        'werkzeug',
        'dotenv'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            spec = importlib.util.find_spec(package)
            if spec is None:
                print(f"❌ {package}")
                missing_packages.append(package)
            else:
                print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ 缺少包: {missing_packages}")
        print("请运行: pip install -r requirements.txt")
        return False
    else:
        print(f"\n✅ 所有依赖包都已安装")
        return True

def check_imports():
    """检查模块导入"""
    print("\n🔗 模块导入检查")
    
    try:
        # 测试基础导入
        from flask import Flask
        print("✅ Flask")
        
        from config import get_config
        print("✅ config")
        
        # 测试应用创建
        sys.path.insert(0, os.getcwd())
        from app import create_app
        print("✅ app")
        
        # 测试数据库
        from app.utils.database import mongo
        print("✅ database")
        
        # 测试模型
        from app.models.user import User
        from app.models.question import Question
        from app.models.response import Response
        print("✅ models")
        
        # 测试路由
        from app.routes.auth import auth_bp
        from app.routes.questionnaire import questionnaire_bp
        print("✅ routes")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def check_database_connection():
    """检查数据库连接"""
    print("\n🗄️ 数据库连接检查")
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.utils.database import check_connection
            is_connected, response_time = check_connection()
            
            if is_connected:
                print(f"✅ 数据库连接成功 (响应时间: {response_time:.2f}ms)")
                return True
            else:
                print("❌ 数据库连接失败")
                return False
                
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False

def test_basic_app_creation():
    """测试基础应用创建"""
    print("\n🚀 应用创建测试")
    
    try:
        from app import create_app
        app = create_app()
        
        if app:
            print("✅ Flask应用创建成功")
            print(f"  - 应用名称: {app.name}")
            print(f"  - 调试模式: {app.debug}")
            print(f"  - 配置加载: {bool(app.config)}")
            return True
        else:
            print("❌ Flask应用创建失败")
            return False
            
    except Exception as e:
        print(f"❌ 应用创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主诊断函数"""
    print("🔍 ProgrammerRoadmap 系统诊断")
    print("=" * 50)
    
    checks = [
        check_python_path,
        check_project_structure,
        check_dependencies,
        check_imports,
        check_database_connection,
        test_basic_app_creation
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ 检查过程出错: {e}")
            results.append(False)
        print()
    
    # 总结
    passed = sum(results)
    total = len(results)
    
    print("=" * 50)
    print(f"📊 诊断完成: {passed}/{total} 项检查通过")
    
    if passed == total:
        print("🎉 系统状态正常，可以启动API服务器")
        print("运行: python run.py")
    else:
        print("⚠️ 发现问题，请根据上述检查结果进行修复")
        
        # 给出建议
        if not results[1]:  # 项目结构问题
            print("\n💡 建议:")
            print("1. 确保所有文件都在正确位置")
            print("2. 检查 app/__init__.py 是否存在")
        
        if not results[2]:  # 依赖问题
            print("\n💡 建议:")
            print("1. 运行: pip install -r requirements.txt")
            print("2. 确保虚拟环境已激活")

if __name__ == "__main__":
    main()