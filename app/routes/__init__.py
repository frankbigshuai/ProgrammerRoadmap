# app/__init__.py
from flask import Flask
from flask_cors import CORS
from config import get_config
from app.utils.database import init_db
import logging
import os

def create_app(config_name=None):
    """应用工厂函数"""
    
    # 创建 Flask 应用
    app = Flask(__name__)
    
    # 加载配置
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    config_class = get_config()[config_name]
    app.config.from_object(config_class)
    
    # 配置日志
    setup_logging(app)
    
    # 初始化扩展
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # 初始化数据库
    init_db(app)
    
    # 注册蓝图（路由）
    register_blueprints(app)
    
    # 错误处理
    register_error_handlers(app)
    
    # 健康检查路由
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'ProgrammerRoadmap API is running'}, 200
    
    return app

def setup_logging(app):
    """设置日志"""
    if not app.debug:
        # 创建日志目录
        log_dir = os.path.dirname(app.config['LOG_FILE'])
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 配置文件日志
        file_handler = logging.FileHandler(app.config['LOG_FILE'])
        file_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))

def register_blueprints(app):
    """注册蓝图"""
    from app.routes.auth import auth_bp
    from app.routes.questionnaire import questionnaire_bp
    from app.routes.responses import responses_bp
    
    api_prefix = f"/api/{app.config['API_VERSION']}"
    
    app.register_blueprint(auth_bp, url_prefix=f"{api_prefix}/auth")
    app.register_blueprint(questionnaire_bp, url_prefix=f"{api_prefix}/questionnaire")
    app.register_blueprint(responses_bp, url_prefix=f"{api_prefix}/responses")

def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(404)
    def not_found(error):
        return {"success": False, "message": "接口不存在"}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {"success": False, "message": "服务器内部错误"}, 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return {"success": False, "message": "请求参数错误"}, 400