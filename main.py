
from flask import Flask
import os

# 创建Flask应用实例
app = Flask(__name__)

# 路由定义
@app.route('/')
def home():
    return '''
    <h1>🚀 程序员学习路线图</h1>
    <h2>欢迎来到ProgrammerRoadmap！</h2>
    <p>这里提供完整的编程学习路径指导</p>
    <ul>
        <li><a href="/frontend">前端开发路线</a></li>
        <li><a href="/backend">后端开发路线</a></li>
        <li><a href="/ai">人工智能路线</a></li>
        <li><a href="/about">关于项目</a></li>
    </ul>
    '''

@app.route('/about')
def about():
    return '''
    <h1>关于 ProgrammerRoadmap</h1>
    <p>🎯 这是一个CS专业AI方向的学习项目</p>
    <p>📚 目标：为编程初学者提供清晰的学习路径</p>
    <p>👨‍💻 适合人群：编程新手、转行人员、在校学生</p>
    '''


@app.route('/api/status')
def status():
    return {
        'status': 'success',
        'message': 'Flask应用运行正常',
        'version': '1.0.0'
    }

if __name__ == '__main__':
    # Railway会设置PORT环境变量
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=False)