# simple_debug.py - 简单调试启动
import traceback

def main():
    print("🚀 启动 ProgrammerRoadmap API")
    print("=" * 40)
    
    try:
        print("📦 导入模块...")
        from app import create_app
        print("✅ 模块导入成功")
        
        print("🏗️ 创建应用...")
        app = create_app()
        print("✅ 应用创建成功")
        
        print("🌍 启动服务器 (http://localhost:8000)")
        print("按 Ctrl+C 停止")
        print("=" * 40)
        
        app.run(
            host='0.0.0.0',
            port=8000,
            debug=True,
            use_reloader=False  # 禁用自动重载
        )
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("详细错误信息:")
        traceback.print_exc()

if __name__ == '__main__':
    main()