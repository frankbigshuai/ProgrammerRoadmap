# config.py - Railway 优化版本
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """基础配置类"""
    
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # MongoDB 配置 - Railway 简化版
    # Railway MongoDB 服务提供 MONGO_URL，这是最标准的方式
    MONGO_URI = (
        os.environ.get('MONGO_URL') or           # Railway MongoDB 服务默认提供
        os.environ.get('DATABASE_URL') or        # 通用数据库变量
        os.environ.get('MONGODB_URI') or         # 备用选项
        'mongodb://localhost:27017/programmer_roadmap'  # 本地开发默认
    )
    
    MONGO_DBNAME = 'programmer_roadmap'
    
    # API配置
    API_VERSION = os.environ.get('API_VERSION', 'v1')
    
    # CORS配置
    CORS_ORIGINS = ['*']  # 生产环境应该设置具体域名
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    # 生产环境的安全配置
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else ['*']

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    MONGO_URI = 'mongodb://localhost:27017/programmer_roadmap_test'
    MONGO_DBNAME = 'programmer_roadmap_test'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': ProductionConfig  # Railway 默认使用生产配置
}

def get_config():
    """获取当前环境配置"""
    # Railway 环境检测
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        return ProductionConfig
    
    # 其他环境
    env = os.environ.get('FLASK_ENV', 'production')
    return config.get(env, config['default'])