# init_data.py - 问卷数据初始化脚本
import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def create_questions():
    """创建问卷题目"""
    from flask import Flask
    from config import get_config
    from app.utils.database import init_db
    from app.models.question import Question
    
    # 创建Flask应用用于数据库操作
    app = Flask(__name__)
    config_class = get_config()
    app.config.from_object(config_class)
    
    with app.app_context():
        # 初始化数据库
        init_db(app)
        print("✅ 数据库连接成功")
        
        # 问卷题目数据
        questions_data = [
            # 🔥 编程经验类
            {
                "question_id": "exp_001",
                "category": "experience", 
                "question_text": "你的编程经验如何？",
                "type": "single_choice",
                "weight": 3,
                "order": 1,
                "options": [
                    {"value": "beginner", "text": "完全没有经验", "score": 1},
                    {"value": "some_basics", "text": "学过一些基础", "score": 2},
                    {"value": "intermediate", "text": "有一定经验", "score": 3},
                    {"value": "experienced", "text": "比较有经验", "score": 4},
                    {"value": "expert", "text": "非常有经验", "score": 5}
                ]
            },
            {
                "question_id": "exp_002",
                "category": "experience",
                "question_text": "你熟悉哪些编程语言？",
                "type": "single_choice", 
                "weight": 2,
                "order": 2,
                "options": [
                    {"value": "none", "text": "都不熟悉", "score": 1},
                    {"value": "python", "text": "Python", "score": 3},
                    {"value": "javascript", "text": "JavaScript", "score": 3},
                    {"value": "java", "text": "Java", "score": 4},
                    {"value": "multiple", "text": "多种语言", "score": 5}
                ]
            },
            
            # 🎯 兴趣方向类
            {
                "question_id": "int_001",
                "category": "interest",
                "question_text": "你对哪个技术领域最感兴趣？",
                "type": "single_choice",
                "weight": 4,
                "order": 3,
                "options": [
                    {"value": "web_frontend", "text": "网页前端开发", "score": 5},
                    {"value": "web_backend", "text": "网页后端开发", "score": 4},
                    {"value": "mobile_dev", "text": "移动应用开发", "score": 3},
                    {"value": "ai_ml", "text": "人工智能/机器学习", "score": 5},
                    {"value": "data_science", "text": "数据科学", "score": 4}
                ]
            },
            {
                "question_id": "int_002", 
                "category": "interest",
                "question_text": "你更喜欢做什么类型的工作？",
                "type": "single_choice",
                "weight": 3,
                "order": 4,
                "options": [
                    {"value": "visual", "text": "视觉界面设计和交互", "score": 5},
                    {"value": "logic", "text": "逻辑算法和数据处理", "score": 4},
                    {"value": "system", "text": "系统架构和性能优化", "score": 3},
                    {"value": "analysis", "text": "数据分析和机器学习", "score": 4}
                ]
            },
            
            # 📚 学习风格类
            {
                "question_id": "learn_001",
                "category": "learning_style",
                "question_text": "你更喜欢哪种学习方式？",
                "type": "single_choice",
                "weight": 2,
                "order": 5,
                "options": [
                    {"value": "visual", "text": "看视频教程", "score": 3},
                    {"value": "reading", "text": "阅读文档和书籍", "score": 4},
                    {"value": "practice", "text": "直接动手实践", "score": 5},
                    {"value": "structured", "text": "系统化课程", "score": 4}
                ]
            },
            
            # 🎯 职业规划类
            {
                "question_id": "career_001",
                "category": "career_goal",
                "question_text": "你的职业目标是？",
                "type": "single_choice",
                "weight": 4,
                "order": 6,
                "options": [
                    {"value": "quick_job", "text": "尽快找到工作", "score": 4},
                    {"value": "skill_expert", "text": "成为技术专家", "score": 5},
                    {"value": "startup", "text": "创业或加入创业公司", "score": 4},
                    {"value": "big_company", "text": "进入大公司", "score": 4}
                ]
            },
            
            # ⏰ 时间投入类
            {
                "question_id": "time_001",
                "category": "time_commitment",
                "question_text": "你每天能投入多少时间学习编程？",
                "type": "single_choice",
                "weight": 3,
                "order": 7,
                "options": [
                    {"value": "less_1h", "text": "少于1小时", "score": 2},
                    {"value": "1_2h", "text": "1-2小时", "score": 3},
                    {"value": "2_4h", "text": "2-4小时", "score": 4},
                    {"value": "4_6h", "text": "4-6小时", "score": 5},
                    {"value": "more_6h", "text": "6小时以上", "score": 5}
                ]
            }
        ]
        
        success_count = 0
        failed_count = 0
        
        print(f"\n📋 开始创建 {len(questions_data)} 个问题...")
        
        for question_data in questions_data:
            try:
                result = Question.create(
                    question_id=question_data["question_id"],
                    category=question_data["category"],
                    question_text=question_data["question_text"],
                    question_type=question_data["type"],
                    options=question_data["options"],
                    weight=question_data["weight"],
                    order=question_data["order"]
                )
                
                if result:
                    print(f"✅ 创建问题: {question_data['question_id']} - {question_data['question_text']}")
                    success_count += 1
                else:
                    print(f"⚠️  问题已存在: {question_data['question_id']}")
                    failed_count += 1
                    
            except Exception as e:
                print(f"❌ 创建问题失败: {question_data['question_id']} - {e}")
                failed_count += 1
        
        print(f"\n📊 创建完成:")
        print(f"✅ 成功: {success_count} 个")
        print(f"⚠️  失败/重复: {failed_count} 个")
        print(f"📝 总计: {len(questions_data)} 个问题")
        
        # 验证创建结果
        questions = Question.get_all_active()
        print(f"\n🔍 验证结果: 数据库中现有 {len(questions)} 个活跃问题")
        
        return len(questions) > 0

def main():
    """主函数"""
    print("🚀 初始化问卷数据...")
    print("="*60)
    
    try:
        success = create_questions()
        
        if success:
            print("\n🎉 数据初始化成功！")
            print("💡 现在可以重新运行测试: python test_all_api.py")
        else:
            print("\n❌ 数据初始化失败")
            
    except Exception as e:
        print(f"\n❌ 初始化过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()