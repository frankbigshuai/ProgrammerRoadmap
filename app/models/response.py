from bson import ObjectId
from datetime import datetime
from typing import List, Dict, Optional

class Response:
    """用户答案模型 - 增强版"""

    @staticmethod
    def _get_mongo():
        """获取mongo实例"""
        from app.utils.database import mongo
        if mongo is None:
            raise RuntimeError("MongoDB connection not initialized")
        return mongo

    @staticmethod
    def save_answer(user_id: str, question_id: str, answer_value: str, 
                   answer_text: str = None) -> bool:
        """保存用户答案 - 支持复杂数据结构"""
        try:
            mongo = Response._get_mongo()
            
            # 获取问题信息用于解析答案
            from app.models.question import Question
            question = Question.get_by_id(question_id)
            if not question:
                print(f"问题不存在: {question_id}")
                return False
            
            # 找到对应的选项数据
            option_data = None
            for option in question.get('options', []):
                if option['value'] == answer_value:
                    option_data = option
                    break
            
            if not option_data:
                print(f"无效的答案选项: {answer_value}")
                return False
            
            answer_record = {
                "user_id": str(user_id),
                "question_id": question_id,
                "question_category": question["category"],
                "answer_value": answer_value,
                "answer_text": answer_text or option_data["text"],
                
                # 根据问题类型存储不同的数据结构
                "skill_mapping": option_data.get("skill_mapping"),
                "path_weights": option_data.get("path_weights"), 
                "goal_mapping": option_data.get("goal_mapping"),
                "style_mapping": option_data.get("style_mapping"),
                "time_mapping": option_data.get("time_mapping"),
                
                # 通用字段
                "tags": option_data.get("tags", []),
                "weight": question.get("weight", 1),
                "score": option_data.get("score", 0),  # 保持向后兼容
                "answered_at": datetime.utcnow()
            }
            
            # 检查是否已有答案（支持修改）
            existing = mongo.db.responses.find_one({
                "user_id": str(user_id),
                "question_id": question_id
            })
            
            if existing:
                # 更新已有答案
                result = mongo.db.responses.update_one(
                    {"user_id": str(user_id), "question_id": question_id},
                    {"$set": answer_record}
                )
                success = result.modified_count > 0
                print(f"答案更新: {'成功' if success else '失败'}")
            else:
                # 新增答案
                result = mongo.db.responses.insert_one(answer_record)
                success = bool(result.inserted_id)
                print(f"答案保存: {'成功' if success else '失败'}")
            
            return success
        except Exception as e:
            print(f"保存答案失败: {e}")
            return False

    @staticmethod
    def get_user_responses(user_id: str) -> List[Dict]:
        """获取用户的所有答案"""
        try:
            mongo = Response._get_mongo()
            responses = list(mongo.db.responses.find(
                {"user_id": str(user_id)}
            ).sort("answered_at", 1))
            
            # 转换ObjectId为字符串
            for response in responses:
                response["_id"] = str(response["_id"])
            
            print(f"用户 {user_id} 有 {len(responses)} 个答案")
            return responses
        except Exception as e:
            print(f"获取用户答案失败: {e}")
            return []

    @staticmethod
    def get_responses_by_category(user_id: str, category: str) -> List[Dict]:
        """根据问题类别获取用户答案"""
        try:
            mongo = Response._get_mongo()
            responses = list(mongo.db.responses.find({
                "user_id": str(user_id),
                "question_category": category
            }).sort("answered_at", 1))
            
            for response in responses:
                response["_id"] = str(response["_id"])
            
            print(f"用户 {user_id} 在 {category} 类别有 {len(responses)} 个答案")
            return responses
        except Exception as e:
            print(f"获取分类答案失败: {e}")
            return []

    @staticmethod
    def get_user_response_by_question(user_id: str, question_id: str) -> Optional[Dict]:
        """获取用户对特定问题的答案"""
        try:
            mongo = Response._get_mongo()
            response = mongo.db.responses.find_one({
                "user_id": str(user_id),
                "question_id": question_id
            })
            
            if response:
                response["_id"] = str(response["_id"])
            
            return response
        except Exception as e:
            print(f"获取特定答案失败: {e}")
            return None

    @staticmethod
    def count_user_responses(user_id: str) -> int:
        """统计用户已回答的问题数量"""
        try:
            mongo = Response._get_mongo()
            count = mongo.db.responses.count_documents({"user_id": str(user_id)})
            print(f"用户 {user_id} 已回答 {count} 个问题")
            return count
        except Exception as e:
            print(f"统计答案数量失败: {e}")
            return 0

    @staticmethod
    def get_user_progress(user_id: str) -> Dict:
        """获取用户答题进度"""
        try:
            from app.models.question import Question
            
            # 获取总问题数
            total_questions = len(Question.get_all_active())
            
            # 获取已回答数
            answered_count = Response.count_user_responses(user_id)
            
            # 计算进度
            progress_percentage = (answered_count / total_questions * 100) if total_questions > 0 else 0
            
            progress = {
                "total_questions": total_questions,
                "answered_count": answered_count,
                "progress_percentage": round(progress_percentage, 1),
                "is_completed": answered_count >= total_questions
            }
            
            print(f"用户进度: {progress_percentage:.1f}%")
            return progress
        except Exception as e:
            print(f"获取进度失败: {e}")
            return {
                "total_questions": 0,
                "answered_count": 0,
                "progress_percentage": 0,
                "is_completed": False
            }

    @staticmethod
    def get_user_profile_data(user_id: str) -> Dict:
        """获取用户完整画像数据"""
        try:
            all_responses = Response.get_user_responses(user_id)
            
            # 按类别分组答案
            profile_data = {
                "skill_assessment": [],
                "interest_preference": [],
                "career_goal": [],
                "learning_style": [],
                "time_planning": []
            }
            
            for response in all_responses:
                category = response.get("question_category")
                if category in profile_data:
                    profile_data[category].append(response)
            
            return {
                "user_id": user_id,
                "profile_data": profile_data,
                "total_responses": len(all_responses),
                "completed_categories": [k for k, v in profile_data.items() if len(v) > 0]
            }
        except Exception as e:
            print(f"获取用户画像失败: {e}")
            return {"user_id": user_id, "profile_data": {}, "total_responses": 0}

    @staticmethod
    def delete_user_responses(user_id: str) -> bool:
        """删除用户的所有答案（重新开始问卷时使用）"""
        try:
            mongo = Response._get_mongo()
            result = mongo.db.responses.delete_many({"user_id": str(user_id)})
            
            success = result.deleted_count > 0
            print(f"删除用户答案: {'成功' if success else '无数据'} ({result.deleted_count} 条)")
            return success
        except Exception as e:
            print(f"删除用户答案失败: {e}")
            return False

    @staticmethod
    def get_responses_for_recommendation(user_id: str) -> Dict:
        """获取用于推荐算法的答案数据"""
        try:
            profile_data = Response.get_user_profile_data(user_id)
            
            # 处理各类别数据
            skill_profile = Response._process_skill_assessment(profile_data["profile_data"].get("skill_assessment", []))
            interest_profile = Response._process_interest_preference(profile_data["profile_data"].get("interest_preference", []))
            goal_profile = Response._process_career_goal(profile_data["profile_data"].get("career_goal", []))
            style_profile = Response._process_learning_style(profile_data["profile_data"].get("learning_style", []))
            time_profile = Response._process_time_planning(profile_data["profile_data"].get("time_planning", []))
            
            result = {
                "user_id": user_id,
                "skill_assessment": skill_profile,
                "interest_preference": interest_profile,
                "career_goal": goal_profile,
                "learning_style": style_profile,
                "time_planning": time_profile,
                "response_count": profile_data["total_responses"]
            }
            
            print(f"推荐数据准备完成，总回答数: {profile_data['total_responses']}")
            return result
        except Exception as e:
            print(f"获取推荐数据失败: {e}")
            return {"user_id": user_id, "response_count": 0}

    @staticmethod
    def _process_skill_assessment(responses: List[Dict]) -> Dict:
        """处理技能评估数据"""
        skill_profile = {
            "frontend": {"level": 0, "foundation": 0, "evidence": []},
            "backend": {"level": 0, "foundation": 0, "evidence": []},
            "mobile": {"level": 0, "foundation": 0, "evidence": []},
            "data_science": {"level": 0, "foundation": 0, "evidence": []}
        }
        
        for response in responses:
            skill_mapping = response.get("skill_mapping", {})
            for path, skills in skill_mapping.items():
                if path == "all_paths":
                    for p in skill_profile.keys():
                        skill_profile[p]["level"] += skills.get("level", 0) * 0.5
                        skill_profile[p]["foundation"] += skills.get("foundation", 0) * 0.5
                        skill_profile[p]["evidence"].append(response["answer_text"])
                elif path in skill_profile:
                    skill_profile[path]["level"] += skills.get("level", 0)
                    skill_profile[path]["foundation"] += skills.get("foundation", 0)
                    skill_profile[path]["evidence"].append(response["answer_text"])
        
        # 归一化分数
        for path in skill_profile:
            skill_profile[path]["level"] = min(1.0, skill_profile[path]["level"])
            skill_profile[path]["foundation"] = min(1.0, skill_profile[path]["foundation"])
        
        return skill_profile

    @staticmethod
    def _process_interest_preference(responses: List[Dict]) -> Dict:
        """处理兴趣偏好数据"""
        interest_scores = {"frontend": 0, "backend": 0, "mobile": 0, "data_science": 0}
        
        for response in responses:
            path_weights = response.get("path_weights", {})
            for path, weight in path_weights.items():
                if path in interest_scores:
                    interest_scores[path] += weight
        
        return interest_scores

    @staticmethod
    def _process_career_goal(responses: List[Dict]) -> Dict:
        """处理职业目标数据"""
        goals = []
        for response in responses:
            goal_mapping = response.get("goal_mapping")
            if goal_mapping:
                goals.append(goal_mapping)
        return {"goals": goals}

    @staticmethod
    def _process_learning_style(responses: List[Dict]) -> Dict:
        """处理学习方式数据"""
        styles = []
        for response in responses:
            style_mapping = response.get("style_mapping")
            if style_mapping:
                styles.append(style_mapping)
        return {"styles": styles}

    @staticmethod
    def _process_time_planning(responses: List[Dict]) -> Dict:
        """处理时间规划数据"""
        plans = []
        for response in responses:
            time_mapping = response.get("time_mapping")
            if time_mapping:
                plans.append(time_mapping)
        return {"plans": plans}

