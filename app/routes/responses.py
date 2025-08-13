# app/routes/responses.py - 带降级模式
from flask import Blueprint, request, jsonify, current_app
from app.models.user import User
from app.models.question import Question
from app.models.response import Response

responses_bp = Blueprint('responses', __name__)

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

@responses_bp.route('/submit', methods=['POST'])
def submit_answer():
    """提交单个问题的答案"""
    try:
        # 验证用户身份
        user_id, error_response, status_code = verify_token_and_get_user()
        if error_response:
            return jsonify(error_response), status_code
        
        # 检查数据库可用性
        if not _check_db_available():
            return jsonify({
                'success': False,
                'message': '答案提交服务暂时不可用，请稍后重试',
                'error_code': 'SERVICE_UNAVAILABLE'
            }), 503
        
        data = request.get_json()
        
        # 获取参数
        question_id = data.get('question_id')
        answer_value = data.get('answer_value')
        answer_text = data.get('answer_text')  # 可选的自定义文本
        
        if not question_id or not answer_value:
            return jsonify({
                'success': False,
                'message': '问题ID和答案不能为空'
            }), 400
        
        # 验证问题是否存在
        question = Question.get_by_id(question_id)
        if not question:
            return jsonify({
                'success': False,
                'message': '问题不存在'
            }), 404
        
        # 验证答案是否有效
        valid_option = None
        for option in question.get('options', []):
            if option['value'] == answer_value:
                valid_option = option
                break
        
        if not valid_option:
            return jsonify({
                'success': False,
                'message': '无效的答案选项'
            }), 400
        
        # 保存答案
        success = Response.save_answer(
            user_id=user_id,
            question_id=question_id,
            answer_value=answer_value,
            answer_text=answer_text
        )
        
        if success:
            # 获取更新后的进度
            progress = Response.get_user_progress(user_id)
            
            # 如果完成所有问题，更新用户状态
            if progress['is_completed']:
                User.mark_questionnaire_completed(user_id)
            
            return jsonify({
                'success': True,
                'message': '答案提交成功',
                'data': {
                    'question_id': question_id,
                    'answer_value': answer_value,
                    'answer_text': answer_text or valid_option['text'],
                    'progress': progress
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '答案保存失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'提交答案失败: {str(e)}'
        }), 500

@responses_bp.route('/batch', methods=['POST'])
def submit_batch_answers():
    """批量提交答案"""
    try:
        # 验证用户身份
        user_id, error_response, status_code = verify_token_and_get_user()
        if error_response:
            return jsonify(error_response), status_code
        
        # 检查数据库可用性
        if not _check_db_available():
            return jsonify({
                'success': False,
                'message': '批量提交服务暂时不可用，请稍后重试',
                'error_code': 'SERVICE_UNAVAILABLE'
            }), 503
        
        data = request.get_json()
        answers = data.get('answers', [])
        
        if not answers:
            return jsonify({
                'success': False,
                'message': '答案列表不能为空'
            }), 400
        
        success_count = 0
        failed_count = 0
        errors = []
        
        for answer in answers:
            question_id = answer.get('question_id')
            answer_value = answer.get('answer_value')
            answer_text = answer.get('answer_text')
            
            if not question_id or not answer_value:
                failed_count += 1
                errors.append(f"问题 {question_id}: 参数不完整")
                continue
            
            # 验证问题
            question = Question.get_by_id(question_id)
            if not question:
                failed_count += 1
                errors.append(f"问题 {question_id}: 问题不存在")
                continue
            
            # 验证答案选项
            valid_option = None
            for option in question.get('options', []):
                if option['value'] == answer_value:
                    valid_option = option
                    break
            
            if not valid_option:
                failed_count += 1
                errors.append(f"问题 {question_id}: 无效的答案选项")
                continue
            
            # 保存答案
            success = Response.save_answer(
                user_id=user_id,
                question_id=question_id,
                answer_value=answer_value,
                answer_text=answer_text
            )
            
            if success:
                success_count += 1
            else:
                failed_count += 1
                errors.append(f"问题 {question_id}: 保存失败")
        
        # 获取更新后的进度
        progress = Response.get_user_progress(user_id)
        
        # 如果完成所有问题，更新用户状态
        if progress['is_completed']:
            User.mark_questionnaire_completed(user_id)
        
        return jsonify({
            'success': True,
            'message': f'批量提交完成，成功 {success_count} 个，失败 {failed_count} 个',
            'data': {
                'success_count': success_count,
                'failed_count': failed_count,
                'total_count': len(answers),
                'errors': errors,
                'progress': progress
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'批量提交失败: {str(e)}'
        }), 500

@responses_bp.route('/my-answers', methods=['GET'])
def get_my_answers():
    """获取用户的所有答案"""
    try:
        # 验证用户身份
        user_id, error_response, status_code = verify_token_and_get_user()
        if error_response:
            return jsonify(error_response), status_code
        
        # 获取用户答案
        responses = Response.get_user_responses(user_id)
        
        return jsonify({
            'success': True,
            'message': '获取答案成功',
            'data': {
                'responses': responses,
                'count': len(responses),
                'is_demo_mode': not _check_db_available()
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取答案失败: {str(e)}'
        }), 500

@responses_bp.route('/profile', methods=['GET'])
def get_user_profile():
    """获取用户画像数据"""
    try:
        # 验证用户身份
        user_id, error_response, status_code = verify_token_and_get_user()
        if error_response:
            return jsonify(error_response), status_code
        
        # 获取用户画像数据
        profile_data = Response.get_user_profile_data(user_id)
        
        return jsonify({
            'success': True,
            'message': '获取用户画像成功',
            'data': profile_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户画像失败: {str(e)}'
        }), 500

@responses_bp.route('/recommendation-data', methods=['GET'])
def get_recommendation_data():
    """获取推荐算法所需的数据"""
    try:
        # 验证用户身份
        user_id, error_response, status_code = verify_token_and_get_user()
        if error_response:
            return jsonify(error_response), status_code
        
        # 获取推荐数据
        recommendation_data = Response.get_responses_for_recommendation(user_id)
        
        return jsonify({
            'success': True,
            'message': '获取推荐数据成功',
            'data': recommendation_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取推荐数据失败: {str(e)}'
        }), 500

@responses_bp.route('/reset', methods=['DELETE'])
def reset_answers():
    """重置用户的所有答案"""
    try:
        # 验证用户身份
        user_id, error_response, status_code = verify_token_and_get_user()
        if error_response:
            return jsonify(error_response), status_code
        
        # 检查数据库可用性
        if not _check_db_available():
            return jsonify({
                'success': False,
                'message': '重置服务暂时不可用，请稍后重试',
                'error_code': 'SERVICE_UNAVAILABLE'
            }), 503
        
        # 删除用户答案
        success = Response.delete_user_responses(user_id)
        
        if success:
            # 重置用户问卷状态
            from app.models.user import User
            from bson import ObjectId
            mongo = Response._get_mongo()
            mongo.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {
                    "questionnaire_completed": False,
                    "questionnaire_completed_at": None
                }}
            )
            
            return jsonify({
                'success': True,
                'message': '答案重置成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '没有找到需要删除的答案'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'重置答案失败: {str(e)}'
        }), 500

@responses_bp.route('/demo-submit', methods=['POST'])
def demo_submit_answer():
    """演示模式提交答案（数据库不可用时使用）"""
    try:
        # 验证用户身份
        user_id, error_response, status_code = verify_token_and_get_user()
        if error_response:
            return jsonify(error_response), status_code
        
        data = request.get_json()
        question_id = data.get('question_id')
        answer_value = data.get('answer_value')
        answer_text = data.get('answer_text')
        
        if not question_id or not answer_value:
            return jsonify({
                'success': False,
                'message': '问题ID和答案不能为空'
            }), 400
        
        # 在演示模式中，只验证格式，不实际保存
        return jsonify({
            'success': True,
            'message': '答案提交成功（演示模式）',
            'data': {
                'question_id': question_id,
                'answer_value': answer_value,
                'answer_text': answer_text,
                'progress': {
                    "total_questions": 3,
                    "answered_count": 1,
                    "progress_percentage": 33.3,
                    "is_completed": False,
                    "is_demo_mode": True
                },
                'is_demo': True
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'演示提交失败: {str(e)}'
        }), 500