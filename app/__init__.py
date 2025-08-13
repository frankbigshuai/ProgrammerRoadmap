# app/__init__.py - 更新健康检查版本
from flask import Flask
from flask_cors import CORS
from app.utils.database import init_db
from config import get_config
import logging
import os

def create_app():
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    config = get_config()
    app.config.from_object(config)
    
    # 启用CORS
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['*']))
    
    # 配置日志
    _setup_logging(app)
    
    # 初始化数据库 - 使用优雅降级
    try:
        init_db(app)
        app.logger.info("✅ 数据库初始化完成")
    except Exception as e:
        app.logger.warning(f"⚠️ 数据库初始化失败，启用降级模式: {e}")
        # 不抛出异常，让应用继续运行
    
    # 注册蓝图
    _register_blueprints(app)
    
    # 注册错误处理
    _register_error_handlers(app)
    
    # 注册健康检查端点
    _register_health_check(app)
    
    app.logger.info("✅ Flask应用创建成功")
    return app

def _register_blueprints(app):
    """注册所有蓝图"""
    try:
        from app.routes.auth import auth_bp
        from app.routes.questionnaire import questionnaire_bp  
        from app.routes.responses import responses_bp
        from app.routes.recommendations import recommendations_bp
        
        # API版本前缀
        api_prefix = f"/api/{app.config.get('API_VERSION', 'v1')}"
        
        # 注册各个蓝图
        app.register_blueprint(auth_bp, url_prefix=f"{api_prefix}/auth")
        app.register_blueprint(questionnaire_bp, url_prefix=f"{api_prefix}/questionnaire")
        app.register_blueprint(responses_bp, url_prefix=f"{api_prefix}/responses")
        app.register_blueprint(recommendations_bp, url_prefix=f"{api_prefix}/recommendations")
        
        app.logger.info("✅ 所有蓝图注册完成")
        
    except ImportError as e:
        app.logger.error(f"❌ 蓝图导入失败: {e}")
        raise e

def _register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(404)
    def not_found(error):
        return {
            'success': False,
            'message': '请求的资源不存在',
            'error_code': 404
        }, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}")
        return {
            'success': False,
            'message': '服务器内部错误',
            'error_code': 500
        }, 500
    
    @app.errorhandler(503)
    def service_unavailable(error):
        return {
            'success': False,
            'message': '服务暂时不可用，请稍后重试',
            'error_code': 503
        }, 503
    
    @app.errorhandler(400)
    def bad_request(error):
        return {
            'success': False,
            'message': '请求参数错误',
            'error_code': 400
        }, 400
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled exception: {error}")
        return {
            'success': False,
            'message': '服务器内部错误',
            'error': str(error) if app.config.get('DEBUG') else 'Internal server error'
        }, 500

def _setup_logging(app):
    """配置日志"""
    # Railway 环境使用标准输出
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        # 生产环境日志配置
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(name)s %(levelname)s: %(message)s'
        )
        app.logger.setLevel(logging.INFO)
    else:
        # 开发环境保留文件日志
        if not app.debug and not os.path.exists('logs'):
            os.makedirs('logs', exist_ok=True)
        
        if not app.debug:
            file_handler = logging.FileHandler('logs/programmer_roadmap.log')
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
    
    app.logger.info('ProgrammerRoadmap API 启动')

def _register_health_check(app):
    """注册健康检查端点"""
    
    @app.route('/')
    def index():
        from app.utils.database import is_db_available
        
        db_status = "connected" if is_db_available() else "degraded"
        
        return {
            'message': 'ProgrammerRoadmap API is running!',
            'version': app.config.get('API_VERSION', 'v1'),
            'service': 'ProgrammerRoadmap API',
            'status': 'healthy',
            'database_status': db_status,
            'endpoints': {
                'health': '/health',
                'auth': '/api/v1/auth',
                'questionnaire': '/api/v1/questionnaire', 
                'responses': '/api/v1/responses',
                'recommendations': '/api/v1/recommendations'
            },
            'demo_endpoints': {
                'demo_login': '/api/v1/auth/demo-login',
                'demo_submit': '/api/v1/responses/demo-submit'
            } if not is_db_available() else {}
        }
    
    @app.route('/health')
    def health_check():
        try:
            from app.utils.database import health_check as db_health_check, is_db_available
            
            db_health = db_health_check()
            overall_status = 'healthy' if db_health['status'] == 'healthy' else 'degraded'
            
            return {
                'status': overall_status,
                'service': 'ProgrammerRoadmap API',
                'version': app.config.get('API_VERSION', 'v1'),
                'database': db_health,
                'database_available': is_db_available(),
                'features': {
                    'user_registration': is_db_available(),
                    'questionnaire_demo': True,
                    'recommendation_engine': True,
                    'data_persistence': is_db_available()
                },
                'timestamp': db_health.get('timestamp')
            }
        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'service': 'ProgrammerRoadmap API',
                'database_available': False
            }, 503