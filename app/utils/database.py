# app/utils/database.py - MongoDB变量调试版
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
    """初始化数据库连接 - 调试版"""
    global _client, _db, mongo
    
    try:
        app.logger.info("🔄 调试MongoDB连接...")
        
        # 显示所有MongoDB相关变量的实际值（用于调试）
        _debug_mongo_variables(app)
        
        # 获取连接URI
        mongo_uri = _get_correct_mongo_uri(app)
        if not mongo_uri:
            raise ValueError("❌ 无法获取MongoDB连接")
        
        # 显示将要使用的连接信息
        app.logger.info(f"📡 尝试连接: {_mask_uri(mongo_uri)}")
        
        # 创建客户端
        _client = MongoClient(mongo_uri, 
                             connectTimeoutMS=10000,
                             serverSelectionTimeoutMS=10000,
                             socketTimeoutMS=10000)
        
        # 选择数据库
        _db = _client['programmer_roadmap']
        
        # 测试连接
        app.logger.info("🏓 测试认证...")
        result = _client.admin.command('ping')
        if result.get('ok') == 1:
            app.logger.info("✅ MongoDB连接和认证成功!")
        
        # 设置全局对象
        mongo.db = _db
        mongo.cx = _client
        
        return mongo
        
    except Exception as e:
        app.logger.error(f"❌ MongoDB连接失败: {e}")
        # 显示可能的解决方案
        _show_auth_troubleshooting(app)
        raise Exception(f"数据库连接失败: {e}")

def _debug_mongo_variables(app):
    """调试MongoDB相关变量"""
    
    app.logger.info("🔍 MongoDB变量调试信息:")
    
    # 所有可能的MongoDB变量名
    mongo_var_names = [
        'MONGO_URL',
        'MONGO_URI', 
        'MONGODB_URI',
        'DATABASE_URL',
        'MONGOHOST',
        'MONGOPORT',
        'MONGOUSER',
        'MONGOPASSWORD',
        'MONGO_INITDB_ROOT_USERNAME',
        'MONGO_INITDB_ROOT_PASSWORD',
        'MONGO_INITDB_DATABASE',
        'MONGO_INITDB_HOST',
        'MONGO_INITDB_PORT'
    ]
    
    found_vars = {}
    for var_name in mongo_var_names:
        value = os.environ.get(var_name)
        if value:
            # 对密码类变量进行部分隐藏
            if 'password' in var_name.lower() or 'pass' in var_name.lower():
                display_value = f"{value[:4]}***{value[-4:]}" if len(value) > 8 else "***"
            else:
                display_value = value
            
            found_vars[var_name] = display_value
            app.logger.info(f"  ✅ {var_name}: {display_value}")
        else:
            app.logger.info(f"  ❌ {var_name}: 未设置")
    
    app.logger.info(f"📊 找到 {len(found_vars)} 个MongoDB变量")
    
    # 如果没有找到任何变量，显示所有环境变量中包含mongo的
    if not found_vars:
        app.logger.warning("⚠️ 未找到标准MongoDB变量，搜索所有相关变量:")
        for key, value in os.environ.items():
            if 'mongo' in key.lower():
                display_value = f"{value[:10]}..." if len(value) > 10 else value
                app.logger.info(f"  🔍 {key}: {display_value}")

def _get_correct_mongo_uri(app):
    """获取正确的MongoDB URI"""
    
    # 方法1: 检查用户手动设置的MONGO_URI
    mongo_uri = os.environ.get('MONGO_URI')
    if mongo_uri and mongo_uri.startswith('mongodb://'):
        app.logger.info("✅ 使用手动设置的MONGO_URI")
        return mongo_uri
    
    # 方法2: 使用Railway自动提供的变量
    railway_combinations = [
        # 组合1: 使用MONGO_URL
        {
            'source': 'MONGO_URL',
            'uri': os.environ.get('MONGO_URL')
        },
        # 组合2: 使用标准Railway变量
        {
            'source': 'Railway标准变量',
            'host': os.environ.get('MONGOHOST'),
            'port': os.environ.get('MONGOPORT', '27017'),
            'user': os.environ.get('MONGO_INITDB_ROOT_USERNAME'),
            'pass': os.environ.get('MONGO_INITDB_ROOT_PASSWORD')
        },
        # 组合3: 使用简化变量名
        {
            'source': 'Railway简化变量',
            'host': os.environ.get('MONGOHOST'),
            'port': os.environ.get('MONGOPORT', '27017'),
            'user': os.environ.get('MONGOUSER'),
            'pass': os.environ.get('MONGOPASSWORD')
        }
    ]
    
    for combo in railway_combinations:
        if 'uri' in combo and combo['uri']:
            # 直接使用提供的URI
            uri = combo['uri']
            if uri.startswith('mongodb://'):
                # 确保包含数据库名
                if '/programmer_roadmap' not in uri:
                    if uri.endswith('/'):
                        uri += 'programmer_roadmap'
                    else:
                        uri += '/programmer_roadmap'
                app.logger.info(f"✅ 使用{combo['source']}")
                return uri
        
        elif all(key in combo for key in ['host', 'user', 'pass']):
            # 从分离变量构建URI
            host = combo['host']
            port = combo['port']
            user = combo['user'] 
            password = combo['pass']
            
            if all([host, user, password]):
                uri = f"mongodb://{user}:{password}@{host}:{port}/programmer_roadmap"
                app.logger.info(f"✅ 从{combo['source']}构建URI")
                return uri
    
    app.logger.error("❌ 无法构建有效的MongoDB URI")
    return None

def _show_auth_troubleshooting(app):
    """显示认证故障排除信息"""
    
    app.logger.error("🔐 认证失败故障排除:")
    app.logger.error("  1. 检查Railway MongoDB服务是否正常运行")
    app.logger.error("  2. 确认用户名和密码正确")
    app.logger.error("  3. 重启MongoDB服务")
    app.logger.error("  4. 检查变量是否从MongoDB服务正确传递")
    
    app.logger.error("💡 建议的修复步骤:")
    app.logger.error("  1. 进入Railway MongoDB服务页面")
    app.logger.error("  2. 查看Variables标签页的实际值")
    app.logger.error("  3. 复制正确的连接信息")
    app.logger.error("  4. 手动设置MONGO_URI环境变量")
    
    # 显示建议的URI格式
    host = os.environ.get('MONGOHOST', 'mongodb-tyss.railway.internal')
    app.logger.error(f"  建议格式: mongodb://用户名:密码@{host}:27017/programmer_roadmap")

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