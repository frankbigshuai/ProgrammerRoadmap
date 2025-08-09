# run.py - 修复版本
import os
import sys
import logging
from app import create_app

# 配置基础日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

def main():
    """主启动函数"""
    try:
        # 创建应用实例
        print("🚀 启动 ProgrammerRoadmap API...")
        app = create_app()
        
        # Railway 部署配置
        port = int(os.environ.get('PORT', 8000))
        host = os.environ.get('HOST', '0.0.0.0')
        debug = app.config.get('DEBUG', False)
        
        # 环境信息
        env = os.environ.get('ENV', os.environ.get('FLASK_ENV', 'development'))
        railway_env = os.environ.get('RAILWAY_ENVIRONMENT')
        
        print(f"📋 环境: {env}")
        print(f"🔧 调试模式: {debug}")
        print(f"🌍 监听地址: {host}:{port}")
        if railway_env:
            print(f"🚂 Railway环境: {railway_env}")
        
        # 检查关键环境变量
        mongo_uri = os.environ.get('MONGO_URI') or os.environ.get('MONGO_URL') or os.environ.get('DATABASE_URL')
        if mongo_uri:
            # 隐藏敏感信息
            safe_uri = mongo_uri.split('@')[0] + '@***' if '@' in mongo_uri else mongo_uri[:20] + '...'
            print(f"📊 数据库: {safe_uri}")
        else:
            print("⚠️ 警告: 未找到数据库连接配置")
        
        # 启动应用
        if __name__ == '__main__':
            # 直接运行
            app.run(
                host=host,
                port=port,
                debug=debug,
                use_reloader=False  # Railway 环境禁用重载器
            )
        else:
            # Gunicorn运行
            print("✅ 应用准备就绪，等待Gunicorn启动...")
            return app
            
    except Exception as e:
        print(f"❌ 应用启动失败: {e}")
        logging.error(f"应用启动失败: {e}")
        sys.exit(1)

# 创建应用实例供Gunicorn使用
app = main()

if __name__ == '__main__':
    # 直接运行模式
    main()