# app/utils/database.py - 直接使用PyMongo版本
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, ConfigurationError
import logging
from datetime import datetime
import time
import os

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
    """初始化数据库连接 - 直接使用PyMongo"""
    global _client, _db, mongo
    
    try:
        app.logger.info("🔄 开始初始化数据库连接...")
        
        # 获取数据库配置
        mongo_uri = app.config.get('MONGO_URI')
        if not mongo_uri:
            # 尝试其他可能的环境变量
            mongo_uri = (
                os.environ.get('MONGO_URL') or 
                os.environ.get('MONGODB_URI') or 
                os.environ.get('DATABASE_URL')
            )
        
        if not mongo_uri:
            raise ValueError("❌ 未找到数据库连接字符串")
        
        # 显示连接信息（隐藏敏感信息）
        safe_uri = _mask_uri(mongo_uri)
        app.logger.info(f"📡 连接数据库: {safe_uri}")
        
        # 解析数据库名
        db_name = app.config.get('MONGO_DBNAME', 'programmer_roadmap')
        if 'mongodb://' in mongo_uri or 'mongodb+srv://' in mongo_uri:
            # 从URI中提取数据库名
            if '/' in mongo_uri.split('?')[0] and mongo_uri.split('?')[0].split('/')[-1]:
                db_name = mongo_uri.split('?')[0].split('/')[-1]
        
        app.logger.info(f"📊 目标数据库: {db_name}")
        
        # 配置连接选项
        connect_options = {
            'connectTimeoutMS': 10000,  # 10秒连接超时
            'serverSelectionTimeoutMS': 10000,  # 10秒服务器选择超时
            'socketTimeoutMS': 10000,  # 10秒socket超时
            'maxPoolSize': 10,
            'minPoolSize': 1,
            'retryWrites': True,
            'w': 'majority'
        }
        
        # 创建MongoDB客户端
        app.logger.info("🏗️ 创建MongoDB客户端...")
        _client = MongoClient(mongo_uri, **connect_options)
        
        # 获取数据库对象
        _db = _client[db_name]
        
        # 测试连接
        app.logger.info("🏓 测试数据库连接...")
        for attempt in range(3):
            try:
                start_time = time.time()
                # 使用admin数据库进行ping测试
                result = _client.admin.command('ping')
                response_time = (time.time() - start_time) * 1000
                
                if result.get('ok') == 1:
                    app.logger.info(f"✅ 数据库连接成功! (响应时间: {response_time:.2f}ms)")
                    break
                else:
                    raise ConnectionFailure("Ping命令返回失败")
                    
            except Exception as e:
                if attempt < 2:
                    app.logger.warning(f"⚠️ 连接尝试 {attempt + 1} 失败，重试中... ({e})")
                    time.sleep(2)
                else:
                    raise e
        
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
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"MongoDB 连接失败: {str(e)}"
        app.logger.error(f"❌ {error_msg}")
        raise Exception(error_msg)
        
    except ConfigurationError as e:
        error_msg = f"MongoDB 配置错误: {str(e)}"
        app.logger.error(f"❌ {error_msg}")
        raise Exception(error_msg)
        
    except Exception as e:
        error_msg = f"数据库初始化失败: {str(e)}"
        app.logger.error(f"❌ {error_msg}")
        raise Exception(error_msg)

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
        return uri[:30] + '...' if len(uri) > 30 else uri
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