# app/models/user.py
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
import re

class User:
    """用户模型 - 专为ProgrammerRoadmap设计"""

    @staticmethod
    def _get_mongo():
        """获取mongo实例"""
        from app.utils.database import mongo
        if mongo is None:
            raise RuntimeError("MongoDB connection not initialized")
        return mongo

    @staticmethod
    def create(username: str, email: str, password: str) -> Optional[str]:
        """创建新用户"""
        try:
            mongo = User._get_mongo()
            
            # 验证邮箱格式
            if not User._is_valid_email(email):
                print("邮箱格式不正确")
                return None
                
            # 检查用户名和邮箱是否已存在
            if mongo.db.users.find_one({"$or": [{"username": username}, {"email": email}]}):
                print("用户名或邮箱已存在")
                return None

            user_id = mongo.db.users.insert_one({
                "username": username,
                "email": email,
                "password_hash": generate_password_hash(password),
                "is_active": True,
                
                # 问卷状态
                "questionnaire_completed": False,
                "questionnaire_completed_at": None,
                
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }).inserted_id
            
            print(f"用户创建成功: {user_id}")
            return str(user_id)
        except Exception as e:
            print(f"创建用户失败: {e}")
            return None

    @staticmethod
    def verify_login(username: str, password: str) -> Optional[str]:
        """通过用户名验证登录"""
        try:
            mongo = User._get_mongo()
            user = mongo.db.users.find_one({"username": username, "is_active": True})
            if user and check_password_hash(user["password_hash"], password):
                print(f"用户名登录成功: {username}")
                return str(user["_id"])
            print(f"用户名登录失败: {username}")
            return None
        except Exception as e:
            print(f"用户名登录验证失败: {e}")
            return None

    @staticmethod
    def verify_email_login(email: str, password: str) -> Optional[str]:
        """通过邮箱验证登录"""
        try:
            mongo = User._get_mongo()
            user = mongo.db.users.find_one({"email": email, "is_active": True})
            if user and check_password_hash(user["password_hash"], password):
                print(f"邮箱登录成功: {email}")
                return str(user["_id"])
            print(f"邮箱登录失败: {email}")
            return None
        except Exception as e:
            print(f"邮箱登录验证失败: {e}")
            return None

    @staticmethod
    def get_profile(user_id: str) -> Optional[Dict]:
        """获取用户资料"""
        try:
            mongo = User._get_mongo()
            user = mongo.db.users.find_one(
                {"_id": ObjectId(user_id), "is_active": True},
                {"password_hash": 0}  # 排除敏感字段
            )
            if not user:
                return None
            
            user["_id"] = str(user["_id"])  # 转换ObjectId为字符串
            return user
        except Exception as e:
            print(f"获取用户资料失败: {e}")
            return None

    @staticmethod
    def mark_questionnaire_completed(user_id: str) -> bool:
        """标记问卷已完成"""
        try:
            mongo = User._get_mongo()
            result = mongo.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {
                    "questionnaire_completed": True,
                    "questionnaire_completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }}
            )
            success = result.modified_count > 0
            print(f"标记问卷完成: {'成功' if success else '失败'}")
            return success
        except Exception as e:
            print(f"标记问卷完成失败: {e}")
            return False

    @staticmethod
    def has_completed_questionnaire(user_id: str) -> bool:
        """检查用户是否已完成问卷"""
        try:
            mongo = User._get_mongo()
            user = mongo.db.users.find_one(
                {"_id": ObjectId(user_id)},
                {"questionnaire_completed": 1}
            )
            completed = user.get("questionnaire_completed", False) if user else False
            print(f"问卷完成状态: {completed}")
            return completed
        except Exception as e:
            print(f"检查问卷状态失败: {e}")
            return False

    # JWT Token 功能
    @staticmethod
    def generate_token(user_id: str, secret_key: str) -> str:
        """生成JWT令牌"""
        try:
            payload = {
                'user_id': str(user_id),
                'exp': datetime.utcnow() + timedelta(days=7)  # 7天过期
            }
            token = jwt.encode(payload, secret_key, algorithm='HS256')
            print(f"Token生成成功")
            return token
        except Exception as e:
            print(f"Token生成失败: {e}")
            return ""

    @staticmethod
    def verify_token(token: str, secret_key: str) -> Optional[str]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            user_id = payload['user_id']
            print(f"Token验证成功: {user_id}")
            return user_id
        except jwt.ExpiredSignatureError:
            print("Token已过期")
            return None
        except jwt.InvalidTokenError:
            print("Token无效")
            return None

    @staticmethod
    def change_password(user_id: str, old_password: str, new_password: str) -> bool:
        """修改密码"""
        try:
            mongo = User._get_mongo()
            user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
            if not user or not check_password_hash(user["password_hash"], old_password):
                print("原密码错误")
                return False
            
            mongo.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {
                    "password_hash": generate_password_hash(new_password),
                    "updated_at": datetime.utcnow()
                }}
            )
            print("密码修改成功")
            return True
        except Exception as e:
            print(f"修改密码失败: {e}")
            return False

    # 工具方法
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def deactivate(user_id: str) -> bool:
        """停用账户（软删除）"""
        try:
            mongo = User._get_mongo()
            result = mongo.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            success = result.modified_count > 0
            print(f"账户停用: {'成功' if success else '失败'}")
            return success
        except Exception as e:
            print(f"停用账户失败: {e}")
            return False