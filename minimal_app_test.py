# minimal_app_test.py
"""
最小化Flask应用测试 - 用于隔离问题
"""
from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

def create_minimal_app():
    """创建最小化Flask应用"""
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/')
    def index():
        return jsonify({
            'status': 'ok',
            'message': 'Minimal Flask app is running!'
        })
    
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'service': 'Minimal Test App'
        })
    
    return app

def create_app_with_db():
    """创建包含数据库的应用"""
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/')
    def index():
        return jsonify({
            'status': 'ok',
            'message': 'App with database connection'
        })
    
    @app.route('/test-db')
    def test_db():
        try:
            # 测试数据库连接
            from app.utils.database import init_db, check_connection
            
            init_db(app)
            if check_connection():
                return jsonify({
                    'status': 'ok',
                    'database': 'connected'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'database': 'disconnected'
                }), 500
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500
    
    return app

def create_app_with_routes():
    """创建包含所有路由的应用"""
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/')
    def index():
        return jsonify({
            'status': 'ok',
            'message': 'App with all routes'
        })
    
    try:
        # 逐步添加组件
        print("1. 加载配置...")
        from config import get_config
        config = get_config()
        app.config.from_object(config)
        
        print("2. 初始化数据库...")
        from app.utils.database import init_db
        init_db(app)
        
        print("3. 注册基础路由...")
        from app.routes.auth import auth_bp
        from app.routes.questionnaire import questionnaire_bp
        from app.routes.responses import responses_bp
        
        api_prefix = f"/api/{app.config.get('API_VERSION', 'v1')}"
        app.register_blueprint(auth_bp, url_prefix=f"{api_prefix}/auth")
        app.register_blueprint(questionnaire_bp, url_prefix=f"{api_prefix}/questionnaire")
        app.register_blueprint(responses_bp, url_prefix=f"{api_prefix}/responses")
        
        print("4. 注册推荐路由...")
        from app.routes.recommendations import recommendations_bp
        app.register_blueprint(recommendations_bp, url_prefix=f"{api_prefix}/recommendations")
        
        @app.route('/test-recommendation-engine')
        def test_engine():
            try:
                from app.services.recommendation_engine import RecommendationEngine
                engine = RecommendationEngine()
                paths = engine.learning_paths
                return jsonify({
                    'status': 'ok',
                    'paths_count': len(paths),
                    'paths': list(paths.keys())
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500
        
        print("✅ 所有组件加载成功")
        
    except Exception as e:
        print(f"❌ 组件加载失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 添加错误端点
        @app.route('/error-info')
        def error_info():
            return jsonify({
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            })
    
    return app

def test_step_by_step():
    """逐步测试每个组件"""
    print("🧪 逐步组件测试")
    print("=" * 40)
    
    # 1. 测试最小应用
    print("\n1️⃣ 测试最小Flask应用...")
    try:
        minimal_app = create_minimal_app()
        print("   ✅ 最小应用创建成功")
    except Exception as e:
        print(f"   ❌ 最小应用创建失败: {e}")
        return
    
    # 2. 测试数据库连接
    print("\n2️⃣ 测试数据库连接...")
    try:
        db_app = create_app_with_db()
        print("   ✅ 数据库应用创建成功")
    except Exception as e:
        print(f"   ❌ 数据库应用创建失败: {e}")
        return
    
    # 3. 测试完整应用
    print("\n3️⃣ 测试完整应用...")
    try:
        full_app = create_app_with_routes()
        print("   ✅ 完整应用创建成功")
        
        # 列出所有路由
        with full_app.app_context():
            routes = []
            for rule in full_app.url_map.iter_rules():
                routes.append(f"{','.join(rule.methods - {'HEAD', 'OPTIONS'})} {rule.rule}")
            
            print(f"   📋 注册的路由数量: {len(routes)}")
            print("   前10个路由:")
            for route in routes[:10]:
                print(f"     • {route}")
    
    except Exception as e:
        print(f"   ❌ 完整应用创建失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_step_by_step()
    
    print(f"\n💡 建议:")
    print(f"1. 如果最小应用测试通过，问题在于数据库或路由")
    print(f"2. 如果数据库测试失败，检查MongoDB连接")
    print(f"3. 如果完整应用失败，检查推荐引擎或路由文件")
    
    # 可选：启动最小应用进行测试
    print(f"\n🚀 启动最小测试应用...")
    try:
        app = create_minimal_app()
        print(f"在浏览器访问: http://localhost:8001")
        app.run(host='0.0.0.0', port=8001, debug=True)
    except KeyboardInterrupt:
        print(f"\n👋 测试应用已停止")