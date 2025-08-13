# app/utils/database.py - Railway MongoDB 连接修复版
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure
import logging
from datetime import datetime
import time
import os
from urllib.parse import quote_plus

# 全局数据库连接
_client = None
_db = None
_db_available = False

class MongoWrapper:
    def __init__(self):
        self.db = None
        self.cx = None
        self.available = False

mongo = MongoWrapper()

def init_db(app):
    """初始化数据库连接 - Railway MongoDB 专用修复版"""
    global _client, _db, _db_available, mongo
    
    try:
        app.logger.info("🔄 初始化MongoDB连接...")
        
        # 获取连接URI
        mongo_uri = _build_mongo_uri(app)
        if not mongo_uri:
            raise ValueError("❌ 无法构建MongoDB连接URI")
        
        app.logger.info(f"📡 连接数据库: {_mask_uri(mongo_uri)}")
        
        # 尝试多种连接配置
        connection_configs = [
            # 配置1: 标准连接
            {
                'authSource': 'admin',
                'authMechanism': 'SCRAM-SHA-1'
            },
            # 配置2: 无认证源
            {
                'authMechanism': 'SCRAM-SHA-1'
            },
            # 配置3: 默认认证
            {
                'authSource': 'admin'
            },
            # 配置4: 最简配置
            {}
        ]
        
        for i, config in enumerate(connection_configs, 1):
            try:
                app.logger.info(f"🔧 尝试连接配置 {i}/4...")
                
                # 创建客户端
                _client = MongoClient(
                    mongo_uri,
                    connectTimeoutMS=20000,
                    serverSelectionTimeoutMS=20000,
                    socketTimeoutMS=30000,
                    maxPoolSize=5,
                    retryWrites=True,
                    **config
                )
                
                # 选择数据库
                _db = _client['programmer_roadmap']
                
                # 测试连接 - 使用多种测试方法
                if _test_database_connection(app, _client, _db):
                    app.logger.info(f"✅ 连接配置 {i} 成功!")
                    _db_available = True
                    mongo.available = True
                    mongo.db = _db
                    mongo.cx = _client
                    
                    # 创建索引
                    _create_indexes(app)
                    return mongo
                
            except Exception as e:
                app.logger.warning(f"⚠️ 连接配置 {i} 失败: {e}")
                if _client:
                    _client.close()
                    _client = None
                continue
        
        # 所有配置都失败
        app.logger.error("❌ 所有连接配置都失败")
        _db_available = False
        mongo.available = False
        mongo.db = None
        mongo.cx = None
        
        return mongo
        
    except Exception as e:
        app.logger.error(f"❌ MongoDB初始化失败: {e}")
        _db_available = False
        mongo.available = False
        return mongo

def _build_mongo_uri(app):
    """构建MongoDB连接URI - Railway优化"""
    
    # 方法1: 直接使用MONGO_URL（最优先）
    mongo_url = os.environ.get('MONGO_URL')
    if mongo_url and mongo_url.startswith('mongodb://'):
        app.logger.info("✅ 使用 MONGO_URL")
        uri = mongo_url
        
        # 确保包含数据库名
        if '/programmer_roadmap' not in uri:
            if uri.endswith('/'):
                uri += 'programmer_roadmap'
            else:
                uri += '/programmer_roadmap'
        return uri
    
    # 方法2: 从分离的环境变量构建
    username = os.environ.get('MONGO_INITDB_ROOT_USERNAME') or os.environ.get('MONGOUSER')
    password = os.environ.get('MONGO_INITDB_ROOT_PASSWORD') or os.environ.get('MONGOPASSWORD')
    host = os.environ.get('MONGOHOST') or os.environ.get('RAILWAY_PRIVATE_DOMAIN')
    port = os.environ.get('MONGOPORT', '27017')
    
    if username and password and host:
        app.logger.info("✅ 从分离变量构建URI")
        
        # URL编码用户名和密码以处理特殊字符
        encoded_username = quote_plus(username)
        encoded_password = quote_plus(password)
        
        constructed_uri = f"mongodb://{encoded_username}:{encoded_password}@{host}:{port}/programmer_roadmap"
        return constructed_uri
    
    # 方法3: 尝试其他变量组合
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('mongodb://'):
        app.logger.info("✅ 使用 DATABASE_URL")
        return database_url
    
    app.logger.error("❌ 无法构建MongoDB连接URI")
    app.logger.error("🔍 可用的环境变量:")
    mongo_vars = ['MONGO_URL', 'DATABASE_URL', 'MONGO_INITDB_ROOT_USERNAME', 
                  'MONGO_INITDB_ROOT_PASSWORD', 'MONGOHOST', 'MONGOUSER', 'MONGOPASSWORD']
    
    for var in mongo_vars:
        value = os.environ.get(var)
        if value:
            display_value = _mask_uri(value) if 'password' not in var.lower() else "***"
            app.logger.error(f"  ✅ {var}: {display_value}")
        else:
            app.logger.error(f"  ❌ {var}: 未设置")
    
    return None

def _test_database_connection(app, client, db):
    """测试数据库连接 - 多种测试方法"""
    
    test_methods = [
        ("admin.ping", lambda: client.admin.command('ping')),
        ("list_databases", lambda: client.list_database_names()),
        ("db.stats", lambda: db.command('dbstats')),
        ("list_collections", lambda: db.list_collection_names()),
        ("simple_find", lambda: list(db.test_collection.find().limit(1)))
    ]
    
    for test_name, test_func in test_methods:
        try:
            app.logger.info(f"🏓 测试: {test_name}")
            start_time = time.time()
            result = test_func()
            response_time = (time.time() - start_time) * 1000
            
            app.logger.info(f"✅ {test_name} 成功 ({response_time:.2f}ms)")
            
            # 如果是ping测试，检查结果
            if test_name == "admin.ping" and isinstance(result, dict):
                if result.get('ok') == 1:
                    return True
            else:
                return True
                
        except OperationFailure as e:
            if e.code == 18:  # 认证失败
                app.logger.error(f"❌ {test_name} 认证失败: {e}")
                return False
            else:
                app.logger.warning(f"⚠️ {test_name} 操作失败: {e}")
                continue
        except Exception as e:
            app.logger.warning(f"⚠️ {test_name} 测试失败: {e}")
            continue
    
    return False

def _create_indexes(app):
    """创建必要的数据库索引"""
    try:
        if not _db_available or not mongo.db:
            return
            
        # 用户集合索引
        mongo.db.users.create_index([("username", 1)], unique=True, background=True)
        mongo.db.users.create_index([("email", 1)], unique=True, background=True)
        
        # 问题集合索引
        mongo.db.questions.create_index([("question_id", 1)], unique=True, background=True)
        mongo.db.questions.create_index([("category", 1), ("order", 1)], background=True)
        
        # 答案集合索引
        mongo.db.responses.create_index([("user_id", 1), ("question_id", 1)], unique=True, background=True)
        mongo.db.responses.create_index([("user_id", 1)], background=True)
        
        # 推荐集合索引
        mongo.db.recommendations.create_index([("user_id", 1)], background=True)
        mongo.db.recommendations.create_index([("created_at", 1)], background=True)
        
        app.logger.info("✅ 数据库索引创建完成")
        
    except Exception as e:
        app.logger.warning(f"⚠️ 索引创建失败: {e}")

def _mask_uri(uri):
    """隐藏URI中的敏感信息"""
    try:
        if '@' in uri and 'mongodb://' in uri:
            parts = uri.split('@')
            if len(parts) >= 2:
                protocol_part = parts[0].split('//')
                if len(protocol_part) >= 2:
                    return f"{protocol_part[0]}//***:***@{parts[1]}"
        return uri[:30] + '...' if len(uri) > 30 else uri
    except:
        return 'mongodb://***'

def is_db_available():
    """检查数据库是否可用"""
    return _db_available and mongo.available

def check_connection():
    """检查数据库连接状态"""
    if not is_db_available():
        return False, None
        
    try:
        start_time = time.time()
        result = _client.admin.command('ping')
        response_time = (time.time() - start_time) * 1000
        return result.get('ok') == 1, response_time
    except Exception:
        return False, None

def get_db_stats():
    """获取数据库统计信息"""
    if not is_db_available():
        return {
            'database': 'unavailable',
            'collections': {},
            'collections_count': 0,
            'status': 'degraded_mode'
        }
    
    try:
        collections = {}
        for name in _db.list_collection_names():
            collections[name] = {
                'count': _db[name].count_documents({})
            }
        
        return {
            'database': _db.name,
            'collections': collections,
            'collections_count': len(collections),
            'status': 'healthy'
        }
    except Exception:
        return {
            'database': 'error',
            'collections': {},
            'collections_count': 0,
            'status': 'error'
        }

def cleanup_expired_data():
    """清理过期数据"""
    if not is_db_available():
        return {'recommendations_cleaned': 0, 'feedback_cleaned': 0}
    
    try:
        # 清理30天前的推荐
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        rec_result = _db.recommendations.delete_many({
            'created_at': {'$lt': cutoff_date}
        })
        
        feedback_result = _db.recommendation_feedback.delete_many({
            'submitted_at': {'$lt': cutoff_date}
        })
        
        return {
            'recommendations_cleaned': rec_result.deleted_count,
            'feedback_cleaned': feedback_result.deleted_count
        }
    except Exception:
        return {'recommendations_cleaned': 0, 'feedback_cleaned': 0}

def health_check():
    """健康检查"""
    try:
        if not _client or not _db:
            return {
                'status': 'error',
                'message': 'MongoDB未初始化',
                'database_available': False,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        if not is_db_available():
            return {
                'status': 'degraded',
                'message': 'MongoDB连接失败，应用运行在降级模式',
                'database_available': False,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        is_connected, response_time = check_connection()
        if not is_connected:
            return {
                'status': 'degraded',
                'message': 'MongoDB连接测试失败',
                'database_available': False,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        stats = get_db_stats()
        
        return {
            'status': 'healthy',
            'connection': {
                'connected': True,
                'response_time_ms': round(response_time, 2) if response_time else None
            },
            'database': _db.name,
            'collections_count': stats['collections_count'],
            'database_available': True,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'database_available': False,
            'timestamp': datetime.utcnow().isoformat()
        }