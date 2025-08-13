# app/routes/questionnaire.py - 带降级模式
from flask import Blueprint, request, jsonify, current_app
from app.models.user import User
from app.models.question import Question
from app.models.response import Response

questionnaire_bp = Blueprint('questionnaire', __name__)

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

def _check_db_available():
    """检查数据库是否可用"""
    from app.utils.database import is_db_available
    return is_db_available()

@questionnaire_bp.route('/questions', methods=['GET'])
def get_questions():
    """获取问卷题目（公开接口，支持可选认证）"""
    try:
        # 尝试获取用户身份，但不强制要求
        user_id = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            user_id = User.verify_token(token, current_app.config['SECRET_KEY'])
        
        # 获取查询参数
        category = request.args.get('category')  # 可选：按分类筛选问题
        
        # 获取问题
        if category:
            questions = Question.get_by_category(category)
        else:
            questions = Question.get_all_active()
        
        if not questions:
            return jsonify({
                'success': False,
                'message': '暂无可用问题'
            }), 404
        
        # 如果用户已登录且数据库可用，添加用户的已有答案
        if user_id and _check_db_available():
            user_responses = Response.get_user_responses(user_id)
            response_dict = {resp['question_id']: resp for resp in user_responses}
            
            # 为每个问题添加用户答案
            for question in questions:
                question['user_answer'] = response_dict.get(question['question_id'])
            
            # 获取进度信息
            progress = Response.get_user_progress(user_id)
        else:
            # 未登录用户或降级模式
            progress = {
                "total_questions": len(questions),
                "answered_count": 0,
                "progress_percentage": 0,
                "is_completed": False,
                "is_demo_mode": not _check_db_available()
            }
            for question in questions:
                question['user_answer'] = None
        
        return jsonify({
            'success': True,
            'message': '获取成功',
            'data': {
                'questions': questions,
                'total_questions': len(questions),
                'progress': progress,
                'user_id': user_id,
                'category': category,
                'is_demo_mode': not _check_db_available()
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取问卷失败: {str(e)}'
        }), 500

@questionnaire_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取问卷分类列表"""
    try:
        categories = Question.get_categories()
        
        # 分类信息
        category_info = {
            "skill_assessment": "技能水平评估",
            "interest_preference": "兴趣偏好",
            "career_goal": "职业目标规划",
            "learning_style": "学习方式偏好",
            "time_planning": "时间安排规划"
        }
        
        result = []
        for category in categories:
            result.append({
                "category": category,
                "name": category_info.get(category, category),
                "question_count": len(Question.get_by_category(category))
            })
        
        return jsonify({
            'success': True,
            'message': '获取分类成功',
            'data': {
                'categories': result,
                'total_categories': len(result),
                'is_demo_mode': not _check_db_available()
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取分类失败: {str(e)}'
        }), 500

@questionnaire_bp.route('/status', methods=['GET'])
def get_questionnaire_status():
    """获取问卷状态"""
    try:
        # 验证用户身份
        user_id, error_response, status_code = verify_token_and_get_user()
        if error_response:
            return jsonify(error_response), status_code
        
        # 检查数据库可用性
        if not _check_db_available():
            return jsonify({
                'success': True,
                'message': '获取状态成功（降级模式）',
                'data': {
                    'overall_progress': {
                        "total_questions": 3,
                        "answered_count": 0,
                        "progress_percentage": 0,
                        "is_completed": False,
                        "is_demo_mode": True
                    },
                    'category_progress': {
                        "skill_assessment": {"total_questions": 1, "answered_questions": 0, "is_completed": False},
                        "interest_preference": {"total_questions": 1, "answered_questions": 0, "is_completed": False},
                        "career_goal": {"total_questions": 1, "answered_questions": 0, "is_completed": False}
                    },
                    'is_demo_mode': True
                }
            }), 200
        
        # 获取进度
        progress = Response.get_user_progress(user_id)
        
        # 获取各分类的完成情况
        categories = Question.get_categories()
        category_progress = {}
        
        for category in categories:
            category_questions = Question.get_by_category(category)
            category_responses = Response.get_responses_by_category(user_id, category)
            
            category_progress[category] = {
                "total_questions": len(category_questions),
                "answered_questions": len(category_responses),
                "is_completed": len(category_responses) >= len(category_questions)
            }
        
        return jsonify({
            'success': True,
            'message': '获取状态成功',
            'data': {
                'overall_progress': progress,
                'category_progress': category_progress,
                'is_demo_mode': False
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取状态失败: {str(e)}'
        }), 500