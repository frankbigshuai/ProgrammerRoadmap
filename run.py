# run.py - Railway 优化版本
import os
import sys
import logging
from app import create_app

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

def create_application():
    """创建应用实例"""
    try:
        print("🚀 启动 ProgrammerRoadmap API...")
        app = create_app()
        
        # 环境信息
        env = os.environ.get('RAILWAY_ENVIRONMENT', 'production')
        port = int(os.environ.get('PORT', 8000))
        
        print(f"📋 环境: {env}")
        print(f"🌍 端口: {port}")
        
        # 检查关键环境变量
        mongo_url = os.environ.get('MONGO_URL')
        if mongo_url:
            print("✅ 数据库连接配置已找到")
        else:
            print("⚠️ 警告: 未找到 MONGO_URL 环境变量")
        
        return app
        
    except Exception as e:
        print(f"❌ 应用创建失败: {e}")
        logging.error(f"应用创建失败: {e}")
        raise e

# 创建应用实例供 Gunicorn 使用
app = create_application()

if __name__ == '__main__':
    # 开发环境直接运行
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)