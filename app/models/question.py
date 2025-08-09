from bson import ObjectId
from datetime import datetime
from typing import List, Dict, Optional

class Question:
    """问卷题目模型 - 增强版"""

    @staticmethod
    def _get_mongo():
        """获取mongo实例"""
        from app.utils.database import mongo
        if mongo is None:
            raise RuntimeError("MongoDB connection not initialized")
        return mongo

    @staticmethod
    def create(question_id: str, category: str, question_text: str,
                question_type: str, options: List[Dict] = None,
                weight: int = 1, order: int = 1, metadata: Dict = None) -> Optional[str]:
        """创建新问题 - 支持多维度数据"""
        try:
            mongo = Question._get_mongo()
            
            # 检查question_id是否已存在
            if mongo.db.questions.find_one({"question_id": question_id}):
                print(f"问题ID已存在: {question_id}")
                return None

            question_data = {
                "question_id": question_id,
                "category": category,  # skill_assessment, interest_preference, career_goal, learning_style, time_planning
                "question_text": question_text,
                "type": question_type,  # single_choice, multiple_choice, text_input
                "options": options or [],
                "weight": weight,
                "order": order,
                "metadata": metadata or {},  # 额外的问题元数据
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = mongo.db.questions.insert_one(question_data)
            print(f"问题创建成功: {question_id}")
            return str(result.inserted_id)
        except Exception as e:
            print(f"创建问题失败: {e}")
            return None

    @staticmethod
    def get_by_id(question_id: str) -> Optional[Dict]:
        """根据question_id获取问题"""
        try:
            mongo = Question._get_mongo()
            question = mongo.db.questions.find_one({"question_id": question_id})
            if question:
                question["_id"] = str(question["_id"])
            return question
        except Exception as e:
            print(f"获取问题失败: {e}")
            return None

    @staticmethod
    def get_all_active() -> List[Dict]:
        """获取所有启用的问题，按order排序"""
        try:
            mongo = Question._get_mongo()
            questions = list(mongo.db.questions.find(
                {"is_active": True}
            ).sort("order", 1))
            
            # 转换ObjectId为字符串
            for question in questions:
                question["_id"] = str(question["_id"])
            
            print(f"获取到 {len(questions)} 个活跃问题")
            return questions
        except Exception as e:
            print(f"获取问题列表失败: {e}")
            return []

    @staticmethod
    def get_by_category(category: str) -> List[Dict]:
        """根据分类获取问题"""
        try:
            mongo = Question._get_mongo()
            questions = list(mongo.db.questions.find(
                {"category": category, "is_active": True}
            ).sort("order", 1))
            
            for question in questions:
                question["_id"] = str(question["_id"])
            
            print(f"分类 {category} 有 {len(questions)} 个问题")
            return questions
        except Exception as e:
            print(f"获取分类问题失败: {e}")
            return []

    @staticmethod
    def get_categories() -> List[str]:
        """获取所有问题分类"""
        try:
            mongo = Question._get_mongo()
            categories = mongo.db.questions.distinct("category", {"is_active": True})
            return list(categories)
        except Exception as e:
            print(f"获取问题分类失败: {e}")
            return []

    @staticmethod
    def deactivate(question_id: str) -> bool:
        """停用问题"""
        try:
            mongo = Question._get_mongo()
            result = mongo.db.questions.update_one(
                {"question_id": question_id},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            
            success = result.modified_count > 0
            print(f"问题停用: {'成功' if success else '失败'}")
            return success
        except Exception as e:
            print(f"停用问题失败: {e}")
            return False
