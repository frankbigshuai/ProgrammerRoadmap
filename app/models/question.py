# app/models/question.py - 带降级模式
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
    def _check_db_available():
        """检查数据库是否可用"""
        from app.utils.database import is_db_available
        return is_db_available()

    @staticmethod
    def create(question_id: str, category: str, question_text: str,
                question_type: str, options: List[Dict] = None,
                weight: int = 1, order: int = 1, metadata: Dict = None) -> Optional[str]:
        """创建新问题 - 支持多维度数据"""
        try:
            if not Question._check_db_available():
                print("数据库服务暂不可用")
                return None
                
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
            if not Question._check_db_available():
                return Question._get_sample_question_by_id(question_id)
                
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
            if not Question._check_db_available():
                print("数据库服务暂不可用，返回示例问题")
                return Question._get_sample_questions()
                
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
            return Question._get_sample_questions()

    @staticmethod
    def get_by_category(category: str) -> List[Dict]:
        """根据分类获取问题"""
        try:
            if not Question._check_db_available():
                return Question._get_sample_questions_by_category(category)
                
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
            return Question._get_sample_questions_by_category(category)

    @staticmethod
    def get_categories() -> List[str]:
        """获取所有问题分类"""
        try:
            if not Question._check_db_available():
                return ["skill_assessment", "interest_preference", "career_goal", "learning_style", "time_planning"]
                
            mongo = Question._get_mongo()
            categories = mongo.db.questions.distinct("category", {"is_active": True})
            return list(categories)
        except Exception as e:
            print(f"获取问题分类失败: {e}")
            return ["skill_assessment", "interest_preference", "career_goal", "learning_style", "time_planning"]

    @staticmethod
    def deactivate(question_id: str) -> bool:
        """停用问题"""
        try:
            if not Question._check_db_available():
                print("数据库服务暂不可用")
                return False
                
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

    # 降级模式的示例数据
    @staticmethod
    def _get_sample_questions() -> List[Dict]:
        """获取示例问题（降级模式使用）"""
        return [
            {
                "_id": "demo_001",
                "question_id": "skill_001",
                "category": "skill_assessment",
                "question_text": "你的编程经验水平如何？",
                "type": "single_choice",
                "order": 1,
                "weight": 2,
                "is_active": True,
                "is_demo": True,
                "options": [
                    {
                        "value": "beginner",
                        "text": "初学者（0-1年编程经验）",
                        "skill_mapping": {
                            "all_paths": {"level": 0.1, "foundation": 0.2}
                        }
                    },
                    {
                        "value": "intermediate", 
                        "text": "中级开发者（1-3年经验）",
                        "skill_mapping": {
                            "all_paths": {"level": 0.5, "foundation": 0.6}
                        }
                    },
                    {
                        "value": "advanced",
                        "text": "高级开发者（3年以上）",
                        "skill_mapping": {
                            "all_paths": {"level": 0.8, "foundation": 0.9}
                        }
                    }
                ]
            },
            {
                "_id": "demo_002",
                "question_id": "interest_001",
                "category": "interest_preference",
                "question_text": "你对哪个技术方向最感兴趣？",
                "type": "single_choice",
                "order": 1,
                "weight": 3,
                "is_active": True,
                "is_demo": True,
                "options": [
                    {
                        "value": "web_frontend",
                        "text": "前端开发 - 创建用户界面和交互",
                        "path_weights": {
                            "frontend": 0.9,
                            "backend": 0.2,
                            "mobile": 0.3,
                            "data_science": 0.1
                        }
                    },
                    {
                        "value": "web_backend",
                        "text": "后端开发 - 服务器逻辑和数据处理",
                        "path_weights": {
                            "frontend": 0.2,
                            "backend": 0.9,
                            "mobile": 0.2,
                            "data_science": 0.3
                        }
                    },
                    {
                        "value": "mobile_dev",
                        "text": "移动开发 - iOS/Android应用",
                        "path_weights": {
                            "frontend": 0.4,
                            "backend": 0.3,
                            "mobile": 0.9,
                            "data_science": 0.1
                        }
                    },
                    {
                        "value": "data_ai",
                        "text": "数据科学/AI - 数据分析和机器学习",
                        "path_weights": {
                            "frontend": 0.1,
                            "backend": 0.4,
                            "mobile": 0.1,
                            "data_science": 0.9
                        }
                    }
                ]
            },
            {
                "_id": "demo_003",
                "question_id": "goal_001",
                "category": "career_goal",
                "question_text": "你的短期职业目标是什么？（1-2年内）",
                "type": "single_choice",
                "order": 1,
                "weight": 3,
                "is_active": True,
                "is_demo": True,
                "options": [
                    {
                        "value": "get_first_job",
                        "text": "获得第一份程序员工作",
                        "goal_mapping": {
                            "timeline": "short",
                            "focus": "employment",
                            "priority": "practical_skills"
                        }
                    },
                    {
                        "value": "switch_career",
                        "text": "转行进入技术领域",
                        "goal_mapping": {
                            "timeline": "short",
                            "focus": "transition",
                            "priority": "foundational_knowledge"
                        }
                    }
                ]
            }
        ]

    @staticmethod
    def _get_sample_questions_by_category(category: str) -> List[Dict]:
        """根据分类获取示例问题"""
        all_samples = Question._get_sample_questions()
        return [q for q in all_samples if q.get("category") == category]

    @staticmethod
    def _get_sample_question_by_id(question_id: str) -> Optional[Dict]:
        """根据ID获取示例问题"""
        all_samples = Question._get_sample_questions()
        for question in all_samples:
            if question.get("question_id") == question_id:
                return question
        return None