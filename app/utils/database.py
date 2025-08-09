# app/utils/database.py - 最终修复版本
from flask_pymongo import PyMongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, ConfigurationError
import logging
from datetime import datetime
import time
import os

# 全局 MongoDB 实例
mongo = None

def init_db(app):
    """初始化数据库连接 - 最终修复版本"""
    global mongo
    
    try:
        app.logger.info("🔄 开始初始化数据库连接...")
        
        # 获取和验证数据库配置
        mongo_uri = app.config.get('MONGO_URI')
        if not mongo_uri:
            raise ValueError("❌ 未找到 MONGO_URI 配置")
        
        # 显示连接信息（隐藏敏感信息）
        safe_uri = mongo_uri.replace(mongo_uri.split('@')[0].split('//')[1], '***:***') if '@' in mongo_uri else mongo_uri[:30] + '...'
        app.logger.info(f"📡 连接数据库: {safe_uri}")
        
        # 设置超时和连接池参数
        app.config.setdefault('MONGO_CONNECT_TIMEOUT_MS', 10000)  # 10秒
        app.config.setdefault('MONGO_SERVER_SELECTION_TIMEOUT_MS', 10000)  # 10秒
        app.config.setdefault('MONGO_SOCKET_TIMEOUT_MS', 10000)  # 10秒
        app.config.setdefault('MONGO_MAX_POOL_SIZE', 10)
        app.config.setdefault('MONGO_MIN_POOL_SIZE', 1)
        
        # 初始化 PyMongo
        mongo = PyMongo()
        mongo.init_app(app)
        
        # 测试连接 - 使用更宽松的超时
        app.logger.info("🏓 测试数据库连接...")
        start_time = time.time()
        
        # 多次重试连接
        for attempt in range(3):
            try:
                result = mongo.db.command('ping')
                if result.get('ok') == 1:
                    response_time = (time.time() - start_time) * 1000
                    app.logger.info(f"✅ 数据库连接成功! (响应时间: {response_time:.2f}ms)")
                    break
                else:
                    raise ConnectionFailure("Ping命令返回失败")
            except Exception as e:
                if attempt < 2:  # 前两次失败重试
                    app.logger.warning(f"⚠️ 连接尝试 {attempt + 1} 失败，重试中... ({e})")
                    time.sleep(2)
                else:
                    raise e
        
        # 获取数据库信息
        try:
            db_name = mongo.db.name
            app.logger.info(f"📊 数据库名称: {db_name}")
        except Exception as e:
            app.logger.warning(f"⚠️ 无法获取数据库名称: {e}")
        
        # 创建索引和初始化数据（非阻塞）
        try:
            _ensure_collections(app)
            _create_indexes(app)
            app.logger.info("✅ 数据库初始化完成")
        except Exception as e:
            app.logger.warning(f"⚠️ 索引创建警告: {e}")
        
        return mongo
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        error_msg = f"MongoDB 连接失败: {str(e)}"
        app.logger.error(f"❌ {error_msg}")
        
        # 在生产环境中的降级处理
        if app.config.get('ENV') == 'production' or os.environ.get('RAILWAY_ENVIRONMENT'):
            app.logger.error("🚨 生产环境数据库连接失败，应用无法启动")
            raise Exception(f"数据库连接必需但失败: {error_msg}")
        else:
            raise e
            
    except ConfigurationError as e:
        app.logger.error(f"❌ 数据库配置错误: {e}")
        raise e
        
    except Exception as e:
        app.logger.error(f"❌ 数据库初始化意外错误: {e}")
        raise e

def _ensure_collections(app):
    """确保必要的集合存在"""
    try:
        if not mongo or not mongo.db:
            app.logger.warning("⚠️ MongoDB实例不可用，跳过集合创建")
            return
            
        db = mongo.db
        required_collections = [
            'users', 'questions', 'responses', 
            'recommendations', 'recommendation_feedback'
        ]
        
        existing_collections = db.list_collection_names()
        
        for collection in required_collections:
            if collection not in existing_collections:
                db.create_collection(collection)
                app.logger.info(f"📁 创建集合: {collection}")
        
        app.logger.info("✅ 集合检查完成")
        
    except Exception as e:
        app.logger.warning(f"⚠️ 集合创建警告: {e}")

def _create_indexes(app):
    """创建数据库索引"""
    try:
        if not mongo or not mongo.db:
            app.logger.warning("⚠️ MongoDB实例不可用，跳过索引创建")
            return
            
        db = mongo.db
        
        # 用户集合索引
        try:
            db.users.create_index("username", unique=True)
            db.users.create_index("email", unique=True)
            db.users.create_index("created_at")
            db.users.create_index([("is_active", 1), ("created_at", -1)])
        except Exception as e:
            app.logger.warning(f"⚠️ 用户索引创建警告: {e}")
        
        # 问题集合索引
        try:
            db.questions.create_index("question_id", unique=True)
            db.questions.create_index([("category", 1), ("order", 1)])
            db.questions.create_index([("is_active", 1), ("order", 1)])
        except Exception as e:
            app.logger.warning(f"⚠️ 问题索引创建警告: {e}")
        
        # 答案集合索引
        try:
            db.responses.create_index([("user_id", 1), ("question_id", 1)], unique=True)
            db.responses.create_index([("user_id", 1), ("answered_at", -1)])
            db.responses.create_index([("user_id", 1), ("question_category", 1)])
        except Exception as e:
            app.logger.warning(f"⚠️ 答案索引创建警告: {e}")
        
        # 推荐结果集合索引
        try:
            db.recommendations.create_index([("user_id", 1), ("created_at", -1)])
            db.recommendations.create_index([("user_id", 1), ("is_active", 1)])
        except Exception as e:
            app.logger.warning(f"⚠️ 推荐索引创建警告: {e}")
        
        # 反馈集合索引
        try:
            db.recommendation_feedback.create_index([("user_id", 1), ("submitted_at", -1)])
        except Exception as e:
            app.logger.warning(f"⚠️ 反馈索引创建警告: {e}")
        
        app.logger.info("✅ 数据库索引创建完成")
        
    except Exception as e:
        app.logger.warning(f"⚠️ 创建索引总体警告: {e}")

def check_connection():
    """检查数据库连接状态"""
    try:
        if not mongo or not mongo.db:
            return False, None
            
        start_time = time.time()
        result = mongo.db.command('ping')
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
        if not mongo or not mongo.db:
            return None
            
        db = mongo.db
        stats = {
            'database': db.name,
            'collections': {},
            'total_size': 0
        }
        
        # 获取各集合统计
        for collection_name in db.list_collection_names():
            try:
                collection_stats = db.command('collStats', collection_name)
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
        if not mongo or not mongo.db:
            return None
            
        db = mongo.db
        from datetime import datetime, timedelta
        
        # 清理超过30天的过期推荐
        expire_date = datetime.utcnow() - timedelta(days=30)
        result = db.recommendations.delete_many({
            'created_at': {'$lt': expire_date},
            'is_active': False
        })
        
        if result.deleted_count > 0:
            logging.info(f"🧹 清理过期推荐: {result.deleted_count} 条")
        
        # 清理超过90天的反馈数据
        old_feedback_date = datetime.utcnow() - timedelta(days=90)
        feedback_result = db.recommendation_feedback.delete_many({
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
        if not mongo or not mongo.db:
            return None
            
        import json
        from datetime import datetime
        
        if not backup_path:
            backup_path = f"backup_{collection_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        db = mongo.db
        collection = db[collection_name]
        
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
        # 检查MongoDB实例
        if not mongo:
            return {
                'status': 'error',
                'message': 'MongoDB实例未初始化',
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