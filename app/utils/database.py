# app/utils/database.py - 快速修复版
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from datetime import datetime
import time
import os

# 全局数据库连接
_client = None
_db = None

class MongoWrapper:
    def __init__(self):
        self.db = None
        self.cx = None

mongo = MongoWrapper()

def init_db(app):
    """初始化数据库连接 - 快速修复版"""
    global _client, _db, mongo
    
    try:
        app.logger.info("🔄 连接MongoDB...")
        
        # 获取并修复URI
        mongo_uri = _get_fixed_mongo_uri(app)
        if not mongo_uri:
            raise ValueError("❌ 无法获取MongoDB连接")
        
        # 显示连接信息
        safe_uri = _mask_uri(mongo_uri)
        app.logger.info(f"📡 连接: {safe_uri}")
        
        # 创建客户端
        _client = MongoClient(mongo_uri, 
                             connectTimeoutMS=30000,
                             serverSelectionTimeoutMS=30000,
                             socketTimeoutMS=30000)
        
        # 选择数据库
        _db = _client['programmer_roadmap']
        
        # 测试连接
        result = _client.admin.command('ping')
        if result.get('ok') == 1:
            app.logger.info("✅ MongoDB连接成功!")
        
        # 设置全局对象
        mongo.db = _db
        mongo.cx = _client
        
        # 创建基本结构
        _setup_basic_structure(app)
        
        return mongo
        
    except Exception as e:
        app.logger.error(f"❌ MongoDB连接失败: {e}")
        raise Exception(f"数据库连接失败: {e}")

def _get_fixed_mongo_uri(app):
    """获取并修复MongoDB URI"""
    
    # 方法1: 检查用户设置的MONGO_URI
    mongo_uri = os.environ.get('MONGO_URI')
    if mongo_uri and mongo_uri.startswith('mongodb://'):
        app.logger.info("✅ 使用MONGO_URI")
        return mongo_uri
    
    # 方法2: 使用Railway的MONGO_URL并修复
    mongo_url = os.environ.get('MONGO_URL')
    if mongo_url and mongo_url.startswith('mongodb://'):
        app.logger.info("✅ 使用MONGO_URL并添加数据库名")
        # 确保以/结尾，然后添加数据库名
        if mongo_url.endswith('/'):
            return mongo_url + 'programmer_roadmap'
        else:
            return mongo_url + '/programmer_roadmap'
    
    # 方法3: 从分离变量构建
    host = os.environ.get('MONGOHOST')
    port = os.environ.get('MONGOPORT', '27017')
    user = os.environ.get('MONGO_INITDB_ROOT_USERNAME') or os.environ.get('MONGOUSER')
    password = os.environ.get('MONGO_INITDB_ROOT_PASSWORD') or os.environ.get('MONGOPASSWORD')
    
    if all([host, user, password]):
        app.logger.info("✅ 从分离变量构建URI")
        return f"mongodb://{user}:{password}@{host}:{port}/programmer_roadmap"
    
    # 显示调试信息
    app.logger.error("❌ 无法构建MongoDB URI")
    app.logger.error("请在Railway中设置以下环境变量:")
    app.logger.error("MONGO_URI=mongodb://mongo:dRqunCnQiYKlpeNsOxMwECWXMYBjYzjO@mongodb-tyss.railway.internal:27017/programmer_roadmap")
    
    return None

def _setup_basic_structure(app):
    """设置基本数据库结构"""
    try:
        # 创建基本集合
        collections = ['users', 'questions', 'responses']
        existing = _db.list_collection_names()
        
        for collection in collections:
            if collection not in existing:
                _db.create_collection(collection)
                app.logger.info(f"📁 创建集合: {collection}")
        
        # 创建基本索引
        try:
            _db.users.create_index("username", unique=True, background=True)
            _db.users.create_index("email", unique=True, background=True)
            app.logger.info("✅ 基本索引创建完成")
        except Exception as e:
            app.logger.warning(f"⚠️ 索引创建: {e}")
            
    except Exception as e:
        app.logger.warning(f"⚠️ 数据库结构设置: {e}")

def _mask_uri(uri):
    """隐藏敏感信息"""
    try:
        if '@' in uri:
            parts = uri.split('@')
            if len(parts) >= 2:
                protocol = parts[0].split('//')[0]
                return f"{protocol}//***:***@{parts[1]}"
        return uri[:50] + '...'
    except:
        return 'mongodb://***'

def check_connection():
    """检查连接"""
    try:
        if not _client:
            return False, None
        start_time = time.time()
        result = _client.admin.command('ping')
        response_time = (time.time() - start_time) * 1000
        return result.get('ok') == 1, response_time
    except:
        return False, None

def get_db_stats():
    """获取统计"""
    try:
        if not _db:
            return None
        return {
            'database': _db.name,
            'collections': {name: {'count': _db[name].count_documents({})} 
                          for name in _db.list_collection_names()},
            'total_size': 0
        }
    except:
        return None

def cleanup_expired_data():
    return {'recommendations_cleaned': 0, 'feedback_cleaned': 0}

def backup_collection(collection_name, backup_path=None):
    return None

def health_check():
    """健康检查"""
    try:
        if not _client or not _db:
            return {
                'status': 'error',
                'message': 'MongoDB未初始化',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        is_connected, response_time = check_connection()
        if not is_connected:
            return {
                'status': 'error',
                'message': 'MongoDB连接失败',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        return {
            'status': 'healthy',
            'connection': {'connected': True, 'response_time_ms': round(response_time, 2)},
            'database': _db.name,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }