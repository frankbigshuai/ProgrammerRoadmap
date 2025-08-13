# app/__init__.py - Railway 优化版本
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
    
    # 初始化数据库
    try:
        init_db(app)
        app.logger.info("✅ 数据库初始化成功")
    except Exception as e:
        app.logger.error(f"❌ 数据库初始化失败: {e}")
        # 在生产环境中，如果数据库连接失败，应该让应用启动失败
        if not app.config.get('DEBUG'):
            raise e
    
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
        return {
            'message': 'ProgrammerRoadmap API is running!',
            'version': app.config.get('API_VERSION', 'v1'),
            'service': 'ProgrammerRoadmap API',
            'status': 'healthy',
            'endpoints': {
                'health': '/health',
                'auth': '/api/v1/auth',
                'questionnaire': '/api/v1/questionnaire', 
                'responses': '/api/v1/responses',
                'recommendations': '/api/v1/recommendations'
            }
        }
    
    @app.route('/health')
    def health_check():
        try:
            from app.utils.database import health_check as db_health_check
            
            db_health = db_health_check()
            
            return {
                'status': 'healthy' if db_health['status'] == 'healthy' else 'unhealthy',
                'service': 'ProgrammerRoadmap API',
                'version': app.config.get('API_VERSION', 'v1'),
                'database': db_health,
                'timestamp': db_health.get('timestamp')
            }
        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'service': 'ProgrammerRoadmap API'
            }, 503