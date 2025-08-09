# app/config.py
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """基础配置类"""
    
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # MongoDB 配置
    MONGO_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/programmer_roadmap'
    MONGO_DBNAME = os.environ.get('MONGODB_DATABASE') or 'programmer_roadmap'
    
    # API配置
    API_VERSION = os.environ.get('API_VERSION', 'v1')
    
    # CORS配置
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else ['*']
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False

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
    'default': DevelopmentConfig
}

def get_config():
    """获取当前环境配置"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config[env]