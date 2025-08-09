# app/routes/recommendations.py
from flask import Blueprint, request, jsonify, current_app
from app.models.user import User
from app.models.response import Response
from app.services.recommendation_engine import RecommendationEngine
from datetime import datetime
import logging

recommendations_bp = Blueprint('recommendations', __name__)

def verify_token_and_get_user():
    """验证Token并获取用户ID的辅助函数"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, {'success': False, 'message': '缺少认证令牌'}, 401
    
    token = auth_header.split(' ')[1]
    user_id = User.verify_token(token, current_app.config['SECRET_KEY'])
    if not user_id:
        return None, {'success': False, 'message': '令牌无效或已过期'}, 401
    
    return user_id, None, None

@recommendations_bp.route('/generate', methods=['POST'])
def generate_recommendation():
    """生成个性化推荐"""
    try:
        # 验证用户身份
        user_id, error_response, status_code = verify_token_and_get_user()
        if error_response:
            return jsonify(error_response), status_code
        
        # 检查用户是否完成了足够的问卷
        user_progress = Response.get_user_progress(user_id)
        if user_progress['answered_count'] < 5:  # 最少需要回答5个问题
            return jsonify({
                'success': False,
                'message': f'需要至少回答5个问题才能生成推荐，当前已回答 {user_progress["answered_count"]} 个',
                'data': {
                    'current_progress': user_progress,
                    'minimum_required': 5
                }
            }), 400
        
        # 获取用户的推荐数据
        user_data = Response.get_responses_for_recommendation(user_id)
        
        if not user_data or user_data.get('response_count', 0) == 0:
            return jsonify({
                'success': False,
                'message': '未找到用户答卷数据'
            }), 404
        
        # 初始化推荐引擎并生成推荐
        engine = RecommendationEngine()
        recommendation = engine.generate_recommendation(user_data)
        
        if not recommendation:
            return jsonify({
                'success': False,
                'message': '推荐生成失败，请稍后重试'
            }), 500
        
        # 可选：保存推荐结果到数据库（用于缓存和分析）
        _save_recommendation_result(user_id, recommendation)
        
        # 标记用户已完成问卷（如果还没标记的话）
        if user_progress['is_completed']:
            User.mark_questionnaire_completed(user_id)
        
        return jsonify({
            'success': True,
            'message': '推荐生成成功',
            'data': {
                'recommendation': recommendation,
                'generated_at': recommendation.get('generated_at'),
                'confidence_score': recommendation.get('confidence_score', 0),
                'user_progress': user_progress
            }
        }), 200
        
    except Exception as e:
        logging.error(f"推荐生成失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'推荐生成失败: {str(e)}'
        }), 500

@recommendations_bp.route('/my-recommendation', methods=['GET'])
def get_my_recommendation():
    """获取用户的最新推荐结果"""
    try:
        # 验证用户身份
        user_id, error_response, status_code = verify_token_and_get_user()
        if error_response:
            return jsonify(error_response), status_code
        
        # 从数据库获取最新的推荐结果
        recommendation = _get_latest_recommendation(user_id)
        
        if not recommendation:
            return jsonify({
                'success': False,
                'message': '未找到推荐结果，请先生成推荐',
                'action_required': 'generate_recommendation'
            }), 404
        
        # 检查推荐是否过期（比如30天）
        if _is_recommendation_expired(recommendation):
            return jsonify({
                'success': False,
                'message': '推荐结果已过期，建议重新生成',
                'data': {
                    'expired_recommendation': recommendation,
                    'action_required': 'regenerate_recommendation'
                }
            }), 200
        
        return jsonify({
            'success': True,
            'message': '获取推荐成功',
            'data': {
                'recommendation': recommendation,
                'is_cached': True
            }
        }), 200
        
    except Exception as e:
        logging.error(f"获取推荐失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取推荐失败: {str(e)}'
        }), 500

@recommendations_bp.route('/learning-paths', methods=['GET'])
def get_available_paths():
    """获取所有可用的学习路径（公开接口）"""
    try:
        engine = RecommendationEngine()
        paths = engine.learning_paths
        
        # 简化路径信息用于展示
        simplified_paths = {}
        for path_key, path_info in paths.items():
            simplified_paths[path_key] = {
                'name': path_info['name'],
                'description': path_info['description'],
                'duration_weeks': path_info['duration_weeks'],
                'difficulty': path_info['difficulty'],
                'core_technologies': path_info['core_technologies'],
                'stages_count': len(path_info['stages'])
            }
        
        return jsonify({
            'success': True,
            'message': '获取学习路径成功',
            'data': {
                'paths': simplified_paths,
                'total_paths': len(simplified_paths)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取学习路径失败: {str(e)}'
        }), 500

@recommendations_bp.route('/path-details/<path_name>', methods=['GET'])
def get_path_details(path_name):
    """获取特定学习路径的详细信息"""
    try:
        engine = RecommendationEngine()
        
        if path_name not in engine.learning_paths:
            return jsonify({
                'success': False,
                'message': f'学习路径 {path_name} 不存在'
            }), 404
        
        path_details = engine.learning_paths[path_name]
        
        return jsonify({
            'success': True,
            'message': '获取路径详细信息成功',
            'data': {
                'path': path_details,
                'path_name': path_name
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取路径详情失败: {str(e)}'
        }), 500

@recommendations_bp.route('/regenerate', methods=['POST'])
def regenerate_recommendation():
    """重新生成推荐（强制刷新）"""
    try:
        # 验证用户身份
        user_id, error_response, status_code = verify_token_and_get_user()
        if error_response:
            return jsonify(error_response), status_code
        
        # 获取用户最新的答卷数据
        user_data = Response.get_responses_for_recommendation(user_id)
        
        if not user_data or user_data.get('response_count', 0) < 3:
            return jsonify({
                'success': False,
                'message': '答卷数据不足，无法生成推荐'
            }), 400
        
        # 删除旧的推荐结果
        _delete_old_recommendations(user_id)
        
        # 生成新推荐
        engine = RecommendationEngine()
        recommendation = engine.generate_recommendation(user_data)
        
        # 保存新推荐结果
        _save_recommendation_result(user_id, recommendation)
        
        return jsonify({
            'success': True,
            'message': '推荐重新生成成功',
            'data': {
                'recommendation': recommendation,
                'regenerated_at': recommendation.get('generated_at')
            }
        }), 200
        
    except Exception as e:
        logging.error(f"重新生成推荐失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'重新生成推荐失败: {str(e)}'
        }), 500

@recommendations_bp.route('/feedback', methods=['POST'])
def submit_recommendation_feedback():
    """提交推荐反馈"""
    try:
        # 验证用户身份
        user_id, error_response, status_code = verify_token_and_get_user()
        if error_response:
            return jsonify(error_response), status_code
        
        data = request.get_json()
        
        # 获取反馈参数
        rating = data.get('rating')  # 1-5星评分
        feedback_text = data.get('feedback', '')
        is_helpful = data.get('is_helpful', True)
        improvement_suggestions = data.get('suggestions', [])
        
        if not rating or not isinstance(rating, int) or not (1 <= rating <= 5):
            return jsonify({
                'success': False,
                'message': '请提供1-5星的评分'
            }), 400
        
        # 保存反馈
        feedback_data = {
            'user_id': user_id,
            'rating': rating,
            'feedback_text': feedback_text,
            'is_helpful': is_helpful,
            'improvement_suggestions': improvement_suggestions,
            'submitted_at': datetime.utcnow()
        }
        
        _save_recommendation_feedback(feedback_data)
        
        return jsonify({
            'success': True,
            'message': '反馈提交成功，感谢您的建议！',
            'data': {
                'rating': rating,
                'feedback_saved': True
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'反馈提交失败: {str(e)}'
        }), 500

# ==================== 辅助函数 ====================

def _save_recommendation_result(user_id: str, recommendation: dict):
    """保存推荐结果到数据库"""
    try:
        from app.utils.database import mongo
        
        # 删除用户的旧推荐记录
        mongo.db.recommendations.delete_many({"user_id": user_id})
        
        # 保存新推荐
        recommendation_record = {
            "user_id": user_id,
            "recommendation_data": recommendation,
            "created_at": datetime.utcnow(),
            "is_active": True,
            "confidence_score": recommendation.get('confidence_score', 0)
        }
        
        result = mongo.db.recommendations.insert_one(recommendation_record)
        print(f"✅ 推荐结果已保存: {result.inserted_id}")
        
    except Exception as e:
        print(f"⚠️ 保存推荐结果失败: {e}")

def _get_latest_recommendation(user_id: str):
    """获取用户最新的推荐结果"""
    try:
        from app.utils.database import mongo
        
        recommendation = mongo.db.recommendations.find_one(
            {"user_id": user_id, "is_active": True},
            sort=[("created_at", -1)]
        )
        
        if recommendation:
            return recommendation.get('recommendation_data')
        return None
        
    except Exception as e:
        print(f"获取推荐结果失败: {e}")
        return None

def _is_recommendation_expired(recommendation: dict, days: int = 30) -> bool:
    """检查推荐是否过期"""
    try:
        generated_at = recommendation.get('generated_at')
        if not generated_at:
            return True
        
        from datetime import datetime, timedelta
        if isinstance(generated_at, str):
            generated_time = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
        else:
            generated_time = generated_at
        
        expiry_time = generated_time + timedelta(days=days)
        return datetime.utcnow() > expiry_time.replace(tzinfo=None)
        
    except Exception as e:
        print(f"检查推荐过期失败: {e}")
        return True

def _delete_old_recommendations(user_id: str):
    """删除用户的旧推荐记录"""
    try:
        from app.utils.database import mongo
        result = mongo.db.recommendations.delete_many({"user_id": user_id})
        print(f"删除了 {result.deleted_count} 条旧推荐记录")
    except Exception as e:
        print(f"删除旧推荐失败: {e}")

def _save_recommendation_feedback(feedback_data: dict):
    """保存推荐反馈"""
    try:
        from app.utils.database import mongo
        result = mongo.db.recommendation_feedback.insert_one(feedback_data)
        print(f"✅ 反馈已保存: {result.inserted_id}")
    except Exception as e:
        print(f"保存反馈失败: {e}")