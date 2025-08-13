# app/routes/auth.py - 带降级模式
from flask import Blueprint, request, jsonify, current_app
from app.models.user import User
import re

auth_bp = Blueprint('auth', __name__)

def _check_db_available():
    """检查数据库是否可用"""
    from app.utils.database import is_db_available
    return is_db_available()

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        # 检查数据库可用性
        if not _check_db_available():
            return jsonify({
                'success': False,
                'message': '注册服务暂时不可用，请稍后重试',
                'error_code': 'SERVICE_UNAVAILABLE'
            }), 503
        
        data = request.get_json()
        
        # 获取参数
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # 基础验证
        if not username or not email or not password:
            return jsonify({
                'success': False,
                'message': '用户名、邮箱和密码不能为空'
            }), 400
        
        # 用户名验证
        if len(username) < 3 or len(username) > 20:
            return jsonify({
                'success': False,
                'message': '用户名长度必须在3-20个字符之间'
            }), 400
        
        # 密码验证
        if len(password) < 6:
            return jsonify({
                'success': False,
                'message': '密码长度不能少于6个字符'
            }), 400
        
        # 创建用户
        user_id = User.create(username, email, password)
        
        if user_id:
            # 生成JWT Token
            token = User.generate_token(user_id, current_app.config['SECRET_KEY'])
            
            return jsonify({
                'success': True,
                'message': '注册成功',
                'data': {
                    'user_id': user_id,
                    'username': username,
                    'email': email,
                    'token': token
                }
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': '用户名或邮箱已存在，或注册服务暂时不可用'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'注册失败: {str(e)}'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        # 检查数据库可用性
        if not _check_db_available():
            return jsonify({
                'success': False,
                'message': '登录服务暂时不可用，请稍后重试',
                'error_code': 'SERVICE_UNAVAILABLE'
            }), 503
        
        data = request.get_json()
        
        # 获取参数
        login_field = data.get('login', '').strip()  # 可以是用户名或邮箱
        password = data.get('password', '')
        
        if not login_field or not password:
            return jsonify({
                'success': False,
                'message': '用户名/邮箱和密码不能为空'
            }), 400
        
        # 判断是邮箱还是用户名
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_email = re.match(email_pattern, login_field)
        
        # 验证登录
        if is_email:
            user_id = User.verify_email_login(login_field, password)
        else:
            user_id = User.verify_login(login_field, password)
        
        if user_id:
            # 获取用户信息
            user_profile = User.get_profile(user_id)
            if not user_profile:
                return jsonify({
                    'success': False,
                    'message': '用户信息获取失败'
                }), 500
            
            # 生成JWT Token
            token = User.generate_token(user_id, current_app.config['SECRET_KEY'])
            
            return jsonify({
                'success': True,
                'message': '登录成功',
                'data': {
                    'user_id': user_id,
                    'username': user_profile['username'],
                    'email': user_profile['email'],
                    'questionnaire_completed': user_profile.get('questionnaire_completed', False),
                    'token': token,
                    'is_demo': user_profile.get('is_demo', False)
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '用户名/邮箱或密码错误'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'登录失败: {str(e)}'
        }), 500

@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    """获取用户资料"""
    try:
        # 从请求头获取Token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'message': '缺少认证令牌'
            }), 401
        
        token = auth_header.split(' ')[1]
        
        # 验证Token
        user_id = User.verify_token(token, current_app.config['SECRET_KEY'])
        if not user_id:
            return jsonify({
                'success': False,
                'message': '令牌无效或已过期'
            }), 401
        
        # 检查数据库可用性
        if not _check_db_available():
            # 返回降级模式的用户信息
            return jsonify({
                'success': True,
                'message': '获取成功（降级模式）',
                'data': {
                    'user_id': user_id,
                    'username': 'demo_user',
                    'email': 'demo@example.com',
                    'questionnaire_completed': False,
                    'created_at': None,
                    'is_demo': True
                }
            }), 200
        
        # 获取用户信息
        user_profile = User.get_profile(user_id)
        if not user_profile:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'message': '获取成功',
            'data': {
                'user_id': user_profile['_id'],
                'username': user_profile['username'],
                'email': user_profile['email'],
                'questionnaire_completed': user_profile.get('questionnaire_completed', False),
                'created_at': user_profile.get('created_at'),
                'is_demo': user_profile.get('is_demo', False)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户信息失败: {str(e)}'
        }), 500

@auth_bp.route('/demo-login', methods=['POST'])
def demo_login():
    """演示模式登录（数据库不可用时使用）"""
    try:
        # 生成演示用户Token
        demo_user_id = "demo_user_123"
        token = User.generate_token(demo_user_id, current_app.config['SECRET_KEY'])
        
        return jsonify({
            'success': True,
            'message': '演示模式登录成功',
            'data': {
                'user_id': demo_user_id,
                'username': 'demo_user',
                'email': 'demo@example.com',
                'questionnaire_completed': False,
                'token': token,
                'is_demo': True
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'演示登录失败: {str(e)}'
        }), 500