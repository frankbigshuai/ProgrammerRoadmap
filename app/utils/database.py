# app/utils/database.py - 优雅降级版
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
_db_available = False

class MongoWrapper:
    def __init__(self):
        self.db = None
        self.cx = None
        self.available = False

mongo = MongoWrapper()

def init_db(app):
    """初始化数据库连接 - 优雅降级版"""
    global _client, _db, _db_available, mongo
    
    try:
        app.logger.info("🔄 初始化MongoDB连接...")
        
        # 获取连接URI
        mongo_uri = _get_mongo_uri(app)
        if not mongo_uri:
            raise ValueError("❌ 无法获取MongoDB连接配置")
        
        # 显示连接信息
        app.logger.info(f"📡 连接数据库: {_mask_uri(mongo_uri)}")
        
        # 创建客户端
        _client = MongoClient(
            mongo_uri,
            connectTimeoutMS=10000,
            serverSelectionTimeoutMS=10000,
            socketTimeoutMS=20000,
            maxPoolSize=10,
            retryWrites=True
        )
        
        # 选择数据库
        _db = _client['programmer_roadmap']
        
        # 尝试测试连接
        app.logger.info("🏓 测试数据库连接...")
        try:
            result = _client.admin.command('ping')
            if result.get('ok') == 1:
                app.logger.info("✅ MongoDB连接和认证成功!")
                _db_available = True
                mongo.available = True
                
                # 创建索引
                _create_indexes(app)
            else:
                raise Exception("Ping 命令返回失败")
                
        except Exception as auth_error:
            app.logger.warning(f"⚠️ MongoDB认证失败，启用降级模式: {auth_error}")
            app.logger.info("📝 应用将在降级模式下运行，数据库操作会返回友好错误")
            _db_available = False
            mongo.available = False
        
        # 无论认证是否成功，都设置连接对象
        mongo.db = _db
        mongo.cx = _client
        
        return mongo
        
    except Exception as e:
        app.logger.error(f"❌ MongoDB连接失败: {e}")
        
        # 设置降级模式
        app.logger.warning("⚠️ 启用数据库降级模式")
        _db_available = False
        mongo.available = False
        mongo.db = None
        mongo.cx = None
        
        # 显示调试信息
        _show_debug_info(app)
        
        # 不抛出异常，让应用继续运行
        return mongo

def _get_mongo_uri(app):
    """获取MongoDB连接URI"""
    
    # 按优先级顺序检查环境变量
    uri_sources = [
        ('MONGO_URL', 'Railway MongoDB服务'),
        ('DATABASE_URL', '通用数据库变量'),
        ('MONGODB_URI', 'MongoDB标准变量'),
        ('MONGO_URI', '自定义变量')
    ]
    
    for var_name, description in uri_sources:
        uri = os.environ.get(var_name)
        if uri and uri.startswith('mongodb'):
            app.logger.info(f"✅ 使用 {description}: {var_name}")
            
            # 确保包含数据库名
            if '/programmer_roadmap' not in uri and not uri.endswith('/'):
                uri += '/programmer_roadmap'
            elif uri.endswith('/') and 'programmer_roadmap' not in uri:
                uri += 'programmer_roadmap'
            
            return uri
    
    # 如果都没有找到
    app.logger.warning("⚠️ 未找到云数据库配置")
    return None

def _create_indexes(app):
    """创建必要的数据库索引"""
    try:
        if not _db_available or not mongo.db:
            return
            
        # 用户集合索引
        mongo.db.users.create_index([("username", 1)], unique=True)
        mongo.db.users.create_index([("email", 1)], unique=True)
        
        # 问题集合索引
        mongo.db.questions.create_index([("question_id", 1)], unique=True)
        mongo.db.questions.create_index([("category", 1), ("order", 1)])
        
        # 答案集合索引
        mongo.db.responses.create_index([("user_id", 1), ("question_id", 1)], unique=True)
        mongo.db.responses.create_index([("user_id", 1)])
        
        # 推荐集合索引
        mongo.db.recommendations.create_index([("user_id", 1)])
        mongo.db.recommendations.create_index([("created_at", 1)])
        
        app.logger.info("✅ 数据库索引创建完成")
        
    except Exception as e:
        app.logger.warning(f"⚠️ 索引创建失败: {e}")

def _show_debug_info(app):
    """显示调试信息"""
    app.logger.error("🔍 调试信息:")
    
    # 检查关键环境变量
    mongo_vars = ['MONGO_URL', 'DATABASE_URL', 'MONGODB_URI', 'MONGO_URI']
    found_vars = 0
    
    for var in mongo_vars:
        value = os.environ.get(var)
        if value:
            found_vars += 1
            app.logger.error(f"  ✅ {var}: {_mask_uri(value)}")
        else:
            app.logger.error(f"  ❌ {var}: 未设置")
    
    if found_vars == 0:
        app.logger.error("❌ 未找到任何MongoDB环境变量")
    
    # Railway 环境特殊提示
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        app.logger.error("🚂 Railway环境故障排除:")
        app.logger.error("  1. 检查MongoDB服务是否完全启动")
        app.logger.error("  2. 尝试重启MongoDB服务")
        app.logger.error("  3. 考虑使用外部MongoDB服务")

def _mask_uri(uri):
    """隐藏URI中的敏感信息"""
    try:
        if '@' in uri:
            parts = uri.split('@')
            if len(parts) >= 2:
                protocol_part = parts[0].split('//')
                if len(protocol_part) >= 2:
                    return f"{protocol_part[0]}//***:***@{parts[1]}"
        return uri[:20] + '...' if len(uri) > 20 else uri
    except:
        return 'mongodb://***'

def is_db_available():
    """检查数据库是否可用"""
    return _db_available and mongo.available

def db_operation_wrapper(operation_name):
    """数据库操作装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not is_db_available():
                return {
                    'success': False,
                    'message': f'数据库服务暂不可用，请稍后重试',
                    'error_code': 'DB_UNAVAILABLE',
                    'operation': operation_name
                }
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return {
                    'success': False,
                    'message': f'数据库操作失败: {str(e)}',
                    'error_code': 'DB_OPERATION_FAILED',
                    'operation': operation_name
                }
        return wrapper
    return decorator

def check_connection():
    """检查数据库连接状态"""
    if not is_db_available():
        return False, None
        
    try:
        start_time = time.time()
        result = _client.server_info()
        response_time = (time.time() - start_time) * 1000
        return True, response_time
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
                'status': 'degraded',
                'message': 'MongoDB未初始化，应用运行在降级模式',
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