# app/utils/database.py - Railway特别优化版本
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, ConfigurationError
import logging
from datetime import datetime
import time
import os
import re

# 全局数据库连接
_client = None
_db = None

class MongoWrapper:
    """模拟Flask-PyMongo的接口"""
    def __init__(self):
        self.db = None
        self.cx = None

# 全局mongo对象，保持兼容性
mongo = MongoWrapper()

def init_db(app):
    """初始化数据库连接 - Railway优化版本"""
    global _client, _db, mongo
    
    try:
        app.logger.info("🔄 开始初始化数据库连接...")
        
        # 获取数据库配置 - Railway特殊处理
        mongo_uri = _get_railway_mongo_uri(app)
        
        if not mongo_uri:
            raise ValueError("❌ 未找到有效的数据库连接字符串")
        
        # 显示连接信息（隐藏敏感信息）
        safe_uri = _mask_uri(mongo_uri)
        app.logger.info(f"📡 连接数据库: {safe_uri}")
        
        # 解析并修复数据库名
        db_name, fixed_uri = _parse_and_fix_uri(mongo_uri, app)
        app.logger.info(f"📊 目标数据库: {db_name}")
        
        # Railway优化的连接选项
        connect_options = {
            'connectTimeoutMS': 15000,  # 15秒连接超时 (Railway网络可能较慢)
            'serverSelectionTimeoutMS': 15000,  # 15秒服务器选择超时
            'socketTimeoutMS': 15000,  # 15秒socket超时
            'maxPoolSize': 5,  # Railway资源有限，减少连接池
            'minPoolSize': 1,
            'retryWrites': True,
            'retryReads': True,
            'maxIdleTimeMS': 30000,  # 30秒空闲超时
            'heartbeatFrequencyMS': 10000,  # 10秒心跳频率
        }
        
        # 创建MongoDB客户端
        app.logger.info("🏗️ 创建MongoDB客户端...")
        _client = MongoClient(fixed_uri, **connect_options)
        
        # 获取数据库对象
        _db = _client[db_name]
        
        # 测试连接 - 增加重试和超时处理
        app.logger.info("🏓 测试数据库连接...")
        _test_connection(app, max_attempts=5, delay=3)
        
        # 设置全局mongo对象
        mongo.db = _db
        mongo.cx = _client
        
        # 验证数据库访问
        try:
            collections = _db.list_collection_names()
            app.logger.info(f"📁 发现 {len(collections)} 个集合")
        except Exception as e:
            app.logger.warning(f"⚠️ 无法列出集合: {e}")
        
        # 创建必要的集合和索引
        try:
            _ensure_collections(app)
            _create_indexes(app)
            app.logger.info("✅ 数据库初始化完成")
        except Exception as e:
            app.logger.warning(f"⚠️ 数据库设置警告: {e}")
        
        return mongo
        
    except Exception as e:
        error_msg = f"数据库初始化失败: {str(e)}"
        app.logger.error(f"❌ {error_msg}")
        
        # 如果是Railway环境，提供更多调试信息
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            app.logger.error("🚂 Railway环境调试信息:")
            app.logger.error(f"  - MONGO_URL: {'✅ 已设置' if os.environ.get('MONGO_URL') else '❌ 未设置'}")
            app.logger.error(f"  - MONGO_URI: {'✅ 已设置' if os.environ.get('MONGO_URI') else '❌ 未设置'}")
            app.logger.error(f"  - DATABASE_URL: {'✅ 已设置' if os.environ.get('DATABASE_URL') else '❌ 未设置'}")
        
        raise Exception(error_msg)

def _get_railway_mongo_uri(app):
    """获取Railway环境的MongoDB URI"""
    # Railway可能的环境变量名
    possible_vars = [
        'MONGO_URI',      # 用户设置的
        'MONGO_URL',      # Railway MongoDB服务
        'DATABASE_URL',   # 通用数据库URL
        'MONGODB_URI',    # 另一种常见命名
        'MONGODB_URL'     # 另一种常见命名
    ]
    
    for var_name in possible_vars:
        uri = os.environ.get(var_name) or app.config.get(var_name)
        if uri:
            app.logger.info(f"📋 使用环境变量: {var_name}")
            
            # 处理Railway模板语法
            if '${' in uri and '}' in uri:
                # 尝试解析Railway模板
                app.logger.warning(f"⚠️ 检测到模板语法: {uri}")
                # 提取模板变量名
                match = re.search(r'\$\{\{([^}]+)\}\}', uri)
                if match:
                    template_var = match.group(1).split('.')[-1]  # 取最后一部分
                    actual_value = os.environ.get(template_var)
                    if actual_value:
                        uri = actual_value
                        app.logger.info(f"✅ 模板解析成功: {template_var}")
                    else:
                        app.logger.error(f"❌ 模板变量未找到: {template_var}")
                        continue
            
            return uri
    
    # 如果都没找到，尝试构建默认URI
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        app.logger.warning("⚠️ 未找到明确的MongoDB URI，尝试默认配置")
        # Railway内部MongoDB的默认格式
        default_uri = "mongodb://mongo:27017/programmer_roadmap"
        app.logger.info(f"🔧 尝试默认URI: {default_uri}")
        return default_uri
    
    return None

def _parse_and_fix_uri(mongo_uri, app):
    """解析并修复MongoDB URI"""
    try:
        # 提取数据库名
        db_name = 'programmer_roadmap'  # 默认数据库名
        
        # 从URI中提取数据库名
        if '/' in mongo_uri:
            uri_parts = mongo_uri.split('?')[0]  # 移除查询参数
            path_part = uri_parts.split('/')[-1]  # 获取路径的最后部分
            if path_part and path_part != '':
                db_name = path_part
                app.logger.info(f"📊 从URI提取数据库名: {db_name}")
        
        # 如果URI没有包含数据库名，添加它
        fixed_uri = mongo_uri
        if not mongo_uri.rstrip('/').split('/')[-1] or mongo_uri.endswith('/'):
            if mongo_uri.endswith('/'):
                fixed_uri = mongo_uri + db_name
            else:
                fixed_uri = mongo_uri + '/' + db_name
            app.logger.info(f"🔧 修复URI，添加数据库名")
        
        # 确保有必要的连接参数
        if 'mongodb+srv://' not in fixed_uri:
            if '?' not in fixed_uri:
                fixed_uri += '?retryWrites=true&w=majority'
            elif 'retryWrites' not in fixed_uri:
                fixed_uri += '&retryWrites=true&w=majority'
        
        return db_name, fixed_uri
        
    except Exception as e:
        app.logger.warning(f"⚠️ URI解析警告: {e}")
        return 'programmer_roadmap', mongo_uri

def _test_connection(app, max_attempts=5, delay=3):
    """测试数据库连接"""
    for attempt in range(max_attempts):
        try:
            start_time = time.time()
            # 使用admin数据库进行ping测试
            result = _client.admin.command('ping')
            response_time = (time.time() - start_time) * 1000
            
            if result.get('ok') == 1:
                app.logger.info(f"✅ 数据库连接成功! (响应时间: {response_time:.2f}ms)")
                return True
            else:
                raise ConnectionFailure("Ping命令返回失败")
                
        except Exception as e:
            if attempt < max_attempts - 1:
                app.logger.warning(f"⚠️ 连接尝试 {attempt + 1} 失败，{delay}秒后重试... ({e})")
                time.sleep(delay)
            else:
                app.logger.error(f"❌ 所有连接尝试都失败了")
                raise e

def _mask_uri(uri):
    """隐藏URI中的敏感信息"""
    try:
        if '@' in uri:
            parts = uri.split('@')
            if len(parts) >= 2:
                # 隐藏用户名密码部分
                prefix = parts[0].split('//')[0] + '//'
                masked_auth = '***:***'
                return prefix + masked_auth + '@' + parts[1]
        return uri[:50] + '...' if len(uri) > 50 else uri
    except:
        return 'mongodb://***'

def _ensure_collections(app):
    """确保必要的集合存在"""
    try:
        if not _db:
            app.logger.warning("⚠️ 数据库实例不可用，跳过集合创建")
            return
            
        required_collections = [
            'users', 'questions', 'responses', 
            'recommendations', 'recommendation_feedback'
        ]
        
        existing_collections = _db.list_collection_names()
        
        for collection in required_collections:
            if collection not in existing_collections:
                _db.create_collection(collection)
                app.logger.info(f"📁 创建集合: {collection}")
        
        app.logger.info("✅ 集合检查完成")
        
    except Exception as e:
        app.logger.warning(f"⚠️ 集合创建警告: {e}")

def _create_indexes(app):
    """创建数据库索引"""
    try:
        if not _db:
            app.logger.warning("⚠️ 数据库实例不可用，跳过索引创建")
            return
        
        # 用户集合索引
        try:
            _db.users.create_index("username", unique=True)
            _db.users.create_index("email", unique=True)
            _db.users.create_index("created_at")
            _db.users.create_index([("is_active", 1), ("created_at", -1)])
            app.logger.info("✅ 用户索引创建完成")
        except Exception as e:
            app.logger.warning(f"⚠️ 用户索引创建警告: {e}")
        
        # 问题集合索引
        try:
            _db.questions.create_index("question_id", unique=True)
            _db.questions.create_index([("category", 1), ("order", 1)])
            _db.questions.create_index([("is_active", 1), ("order", 1)])
            app.logger.info("✅ 问题索引创建完成")
        except Exception as e:
            app.logger.warning(f"⚠️ 问题索引创建警告: {e}")
        
        # 答案集合索引
        try:
            _db.responses.create_index([("user_id", 1), ("question_id", 1)], unique=True)
            _db.responses.create_index([("user_id", 1), ("answered_at", -1)])
            _db.responses.create_index([("user_id", 1), ("question_category", 1)])
            app.logger.info("✅ 答案索引创建完成")
        except Exception as e:
            app.logger.warning(f"⚠️ 答案索引创建警告: {e}")
        
        # 推荐结果集合索引
        try:
            _db.recommendations.create_index([("user_id", 1), ("created_at", -1)])
            _db.recommendations.create_index([("user_id", 1), ("is_active", 1)])
            app.logger.info("✅ 推荐索引创建完成")
        except Exception as e:
            app.logger.warning(f"⚠️ 推荐索引创建警告: {e}")
        
        # 反馈集合索引
        try:
            _db.recommendation_feedback.create_index([("user_id", 1), ("submitted_at", -1)])
            app.logger.info("✅ 反馈索引创建完成")
        except Exception as e:
            app.logger.warning(f"⚠️ 反馈索引创建警告: {e}")
        
        app.logger.info("✅ 所有索引创建完成")
        
    except Exception as e:
        app.logger.warning(f"⚠️ 创建索引总体警告: {e}")

def check_connection():
    """检查数据库连接状态"""
    try:
        if not _client or not _db:
            return False, None
            
        start_time = time.time()
        result = _client.admin.command('ping')
        response_time = (time.time() - start_time) * 1000
        
        if result.get('ok') == 1:
            logging.info(f"🏓 数据库连接正常 (响应时间: {response_time:.2f}ms)")
            return True, response_time
        else:
            return False, None
            
    except Exception as e:
        logging.error(f"❌ 数据库连接检查失败: {e}")
        return False, None

def get_db_stats():
    """获取数据库统计信息"""
    try:
        if not _db:
            return None
            
        stats = {
            'database': _db.name,
            'collections': {},
            'total_size': 0
        }
        
        # 获取各集合统计
        for collection_name in _db.list_collection_names():
            try:
                collection_stats = _db.command('collStats', collection_name)
                stats['collections'][collection_name] = {
                    'count': collection_stats.get('count', 0),
                    'size': collection_stats.get('size', 0),
                    'avgObjSize': collection_stats.get('avgObjSize', 0)
                }
                stats['total_size'] += collection_stats.get('size', 0)
            except Exception as e:
                logging.warning(f"获取集合 {collection_name} 统计失败: {e}")
        
        return stats
        
    except Exception as e:
        logging.error(f"获取数据库统计失败: {e}")
        return None

def cleanup_expired_data():
    """清理过期数据"""
    try:
        if not _db:
            return None
            
        from datetime import datetime, timedelta
        
        # 清理超过30天的过期推荐
        expire_date = datetime.utcnow() - timedelta(days=30)
        result = _db.recommendations.delete_many({
            'created_at': {'$lt': expire_date},
            'is_active': False
        })
        
        if result.deleted_count > 0:
            logging.info(f"🧹 清理过期推荐: {result.deleted_count} 条")
        
        # 清理超过90天的反馈数据
        old_feedback_date = datetime.utcnow() - timedelta(days=90)
        feedback_result = _db.recommendation_feedback.delete_many({
            'submitted_at': {'$lt': old_feedback_date}
        })
        
        if feedback_result.deleted_count > 0:
            logging.info(f"🧹 清理过期反馈: {feedback_result.deleted_count} 条")
            
        return {
            'recommendations_cleaned': result.deleted_count,
            'feedback_cleaned': feedback_result.deleted_count
        }
        
    except Exception as e:
        logging.error(f"清理过期数据失败: {e}")
        return None

def backup_collection(collection_name, backup_path=None):
    """备份指定集合"""
    try:
        if not _db:
            return None
            
        import json
        from datetime import datetime
        
        if not backup_path:
            backup_path = f"backup_{collection_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        collection = _db[collection_name]
        
        # 导出数据
        data = []
        for doc in collection.find():
            # 转换ObjectId为字符串
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            # 转换datetime为ISO格式
            for key, value in doc.items():
                if isinstance(value, datetime):
                    doc[key] = value.isoformat()
            data.append(doc)
        
        # 保存到文件
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"💾 集合 {collection_name} 备份完成: {backup_path}")
        return backup_path
        
    except Exception as e:
        logging.error(f"备份集合失败: {e}")
        return None

def health_check():
    """数据库健康检查"""
    try:
        # 检查客户端
        if not _client or not _db:
            return {
                'status': 'error',
                'message': 'MongoDB客户端未初始化',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # 检查连接
        is_connected, response_time = check_connection()
        if not is_connected:
            return {
                'status': 'error',
                'message': '数据库连接失败',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # 获取统计信息
        stats = get_db_stats()
        
        return {
            'status': 'healthy',
            'connection': {
                'connected': True,
                'response_time_ms': round(response_time, 2) if response_time else None
            },
            'database': stats['database'] if stats else None,
            'collections_count': len(stats['collections']) if stats else 0,
            'total_size_bytes': stats['total_size'] if stats else 0,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }