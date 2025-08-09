# app/utils/database.py - 改进版本
from flask_pymongo import PyMongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from datetime import datetime

# 全局 MongoDB 实例
mongo = PyMongo()

def init_db(app):
    """初始化数据库连接"""
    try:
        # 配置连接参数
        app.config.setdefault('MONGO_CONNECT_TIMEOUT_MS', 5000)
        app.config.setdefault('MONGO_SERVER_SELECTION_TIMEOUT_MS', 5000)
        app.config.setdefault('MONGO_SOCKET_TIMEOUT_MS', 5000)
        app.config.setdefault('MONGO_MAX_POOL_SIZE', 50)
        app.config.setdefault('MONGO_MIN_POOL_SIZE', 5)
        
        mongo.init_app(app)
        
        # 测试连接
        mongo.db.command('ping')
        app.logger.info("✅ MongoDB 连接成功")
        
        # 创建索引和初始化数据
        _create_indexes()
        _ensure_collections()
        
        return mongo
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        app.logger.error(f"❌ MongoDB 连接失败: {e}")
        raise e
    except Exception as e:
        app.logger.error(f"❌ 数据库初始化失败: {e}")
        raise e

def _create_indexes():
    """创建数据库索引"""
    try:
        db = mongo.db
        
        # 用户集合索引
        db.users.create_index("username", unique=True)
        db.users.create_index("email", unique=True)
        db.users.create_index("created_at")
        db.users.create_index([("is_active", 1), ("created_at", -1)])
        
        # 问题集合索引
        db.questions.create_index("question_id", unique=True)
        db.questions.create_index([("category", 1), ("order", 1)])
        db.questions.create_index([("is_active", 1), ("order", 1)])
        
        # 答案集合索引
        db.responses.create_index([("user_id", 1), ("question_id", 1)], unique=True)
        db.responses.create_index([("user_id", 1), ("answered_at", -1)])
        db.responses.create_index([("user_id", 1), ("question_category", 1)])
        
        # 推荐结果集合索引
        db.recommendations.create_index([("user_id", 1), ("created_at", -1)])
        db.recommendations.create_index([("user_id", 1), ("is_active", 1)])
        
        # 反馈集合索引
        db.recommendation_feedback.create_index([("user_id", 1), ("submitted_at", -1)])
        
        logging.info("✅ 数据库索引创建成功")
        
    except Exception as e:
        logging.warning(f"⚠️ 创建索引警告: {e}")

def _ensure_collections():
    """确保必要的集合存在"""
    try:
        db = mongo.db
        required_collections = [
            'users', 'questions', 'responses', 
            'recommendations', 'recommendation_feedback'
        ]
        
        existing_collections = db.list_collection_names()
        
        for collection in required_collections:
            if collection not in existing_collections:
                db.create_collection(collection)
                logging.info(f"📁 创建集合: {collection}")
        
        logging.info("✅ 集合检查完成")
        
    except Exception as e:
        logging.warning(f"⚠️ 集合创建警告: {e}")

def check_connection():
    """检查数据库连接状态"""
    try:
        start_time = datetime.now()
        mongo.db.command('ping')
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        logging.info(f"🏓 数据库连接正常 (响应时间: {response_time:.2f}ms)")
        return True, response_time
        
    except Exception as e:
        logging.error(f"❌ 数据库连接失败: {e}")
        return False, None

def get_db_stats():
    """获取数据库统计信息"""
    try:
        db = mongo.db
        stats = {
            'database': db.name,
            'collections': {},
            'total_size': 0
        }
        
        # 获取各集合统计
        for collection_name in db.list_collection_names():
            collection_stats = db.command('collStats', collection_name)
            stats['collections'][collection_name] = {
                'count': collection_stats.get('count', 0),
                'size': collection_stats.get('size', 0),
                'avgObjSize': collection_stats.get('avgObjSize', 0)
            }
            stats['total_size'] += collection_stats.get('size', 0)
        
        return stats
        
    except Exception as e:
        logging.error(f"获取数据库统计失败: {e}")
        return None

def cleanup_expired_data():
    """清理过期数据"""
    try:
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

# 健康检查函数
def health_check():
    """数据库健康检查"""
    try:
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
                'response_time_ms': response_time
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