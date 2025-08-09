# run.py - Railway 部署版本
from app import create_app
import os

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    # Railway 部署配置
    port = int(os.environ.get('PORT', 8000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    # 生产环境日志
    if not app.config.get('DEBUG', False):
        import logging
        logging.basicConfig(level=logging.INFO)
        app.logger.setLevel(logging.INFO)
        app.logger.info('🚀 ProgrammerRoadmap API 启动中...')
        app.logger.info(f'📋 环境: {app.config.get("ENV", "production")}')
        app.logger.info(f'🌍 监听地址: {host}:{port}')
    else:
        print("🚀 启动 ProgrammerRoadmap API...")
        print(f"📋 环境: {app.config.get('ENV', 'development')}")
        print(f"🔧 调试模式: {app.config.get('DEBUG', False)}")
        print(f"🌍 启动地址: http://localhost:{port}")
    
    # 启动应用
    app.run(
        host=host,
        port=port,
        debug=app.config.get('DEBUG', False),
        use_reloader=False  # Railway 环境禁用重载器
    )