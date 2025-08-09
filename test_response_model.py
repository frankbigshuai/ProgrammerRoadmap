# test_response_simple.py
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_response_model():
    """测试Response模型"""
    print("🚀 开始测试Response模型...\n")
    
    try:
        # 初始化
        from flask import Flask
        from config import DevelopmentConfig
        from app.utils.database import init_db
        from app.models.user import User
        from app.models.question import Question
        from app.models.response import Response
        
        app = Flask(__name__)
        app.config.from_object(DevelopmentConfig)
        
        with app.app_context():
            init_db(app)
            
            print("📝 准备测试数据...")
            # 创建测试用户（使用时间戳避免重复）
            timestamp = str(int(time.time()))
            test_username = f"response_user_{timestamp}"
            test_email = f"response_{timestamp}@test.com"
            
            user_id = User.create(test_username, test_email, "password123")
            if not user_id:
                print("❌ 创建测试用户失败")
                return False
            print(f"✅ 创建测试用户: {user_id}")
            
            # 创建测试问题
            q1_id = Question.create(
                question_id=f"test_q1_{timestamp}",
                category="experience",
                question_text="您的编程基础如何？",
                question_type="single_choice",
                options=[
                    {"value": "beginner", "text": "初学者", "score": 1},
                    {"value": "intermediate", "text": "中级", "score": 2},
                    {"value": "advanced", "text": "高级", "score": 3}
                ],
                weight=10,
                order=1
            )
            
            q2_id = Question.create(
                question_id=f"test_q2_{timestamp}",
                category="interest",
                question_text="您感兴趣的方向？",
                question_type="single_choice",
                options=[
                    {"value": "web", "text": "网页开发", "score": 1},
                    {"value": "mobile", "text": "移动开发", "score": 1}
                ],
                weight=15,
                order=2
            )
            
            if not q1_id or not q2_id:
                print("❌ 创建测试问题失败")
                return False
            print("✅ 创建测试问题成功")
            
            print("\n📝 测试1: 保存用户答案")
            # 保存第一个答案
            success1 = Response.save_answer(
                user_id=user_id,
                question_id=f"test_q1_{timestamp}",
                answer_value="beginner",
                answer_text="初学者",
                score=1
            )
            
            if success1:
                print("✅ 第一个答案保存成功")
            else:
                print("❌ 第一个答案保存失败")
                return False
            
            print("\n📝 测试2: 保存第二个答案")
            # 保存第二个答案
            success2 = Response.save_answer(
                user_id=user_id,
                question_id=f"test_q2_{timestamp}",
                answer_value="web",
                answer_text="网页开发",
                score=1
            )
            
            if success2:
                print("✅ 第二个答案保存成功")
            else:
                print("❌ 第二个答案保存失败")
            
            print("\n📝 测试3: 获取特定问题答案")
            # 获取特定答案
            response = Response.get_user_response_by_question(user_id, f"test_q1_{timestamp}")
            if response and response["answer_value"] == "beginner":
                print("✅ 特定答案获取成功")
            else:
                print("❌ 特定答案获取失败")
            
            print("\n📝 测试4: 获取用户所有答案")
            # 获取所有答案
            all_responses = Response.get_user_responses(user_id)
            if len(all_responses) >= 2:
                print(f"✅ 获取到 {len(all_responses)} 个答案")
            else:
                print(f"❌ 答案数量不正确，期望>=2，实际{len(all_responses)}")
            
            print("\n📝 测试5: 更新答案")
            # 更新答案（用户改选）
            update_success = Response.save_answer(
                user_id=user_id,
                question_id=f"test_q1_{timestamp}",
                answer_value="advanced",
                answer_text="高级",
                score=3
            )
            
            if update_success:
                # 验证更新
                updated_response = Response.get_user_response_by_question(user_id, f"test_q1_{timestamp}")
                if updated_response["answer_value"] == "advanced":
                    print("✅ 答案更新成功")
                else:
                    print("❌ 答案更新验证失败")
            else:
                print("❌ 答案更新失败")
            
            print("\n📝 测试6: 统计答案数量")
            # 统计答案
            count = Response.count_user_responses(user_id)
            if count >= 2:
                print(f"✅ 答案统计正确: {count} 个")
            else:
                print(f"❌ 答案统计错误: {count} 个")
            
            print("\n📝 测试7: 获取答题进度")
            # 获取进度
            progress = Response.get_user_progress(user_id)
            if progress["answered_count"] > 0:
                print(f"✅ 答题进度: {progress['answered_count']}/{progress['total_questions']} ({progress['progress_percentage']}%)")
            else:
                print("❌ 进度获取失败")
            
            print("\n📝 测试8: 获取推荐数据")
            # 获取推荐数据
            recommendation_data = Response.get_responses_for_recommendation(user_id)
            if recommendation_data["response_count"] > 0:
                print(f"✅ 推荐数据准备完成")
                print(f"   - 答案数量: {recommendation_data['response_count']}")
                print(f"   - 总分: {recommendation_data['total_score']}")
                print(f"   - 分类数: {len(recommendation_data['categories'])}")
            else:
                print("❌ 推荐数据获取失败")
            
            print("\n📝 测试9: 清理测试数据")
            # 清理数据
            Response.delete_user_responses(user_id)
            User.deactivate(user_id)
            Question.deactivate(f"test_q1_{timestamp}")
            Question.deactivate(f"test_q2_{timestamp}")
            print("✅ 测试数据清理完成")
            
            print("\n" + "="*50)
            print("🎉 Response模型测试全部完成！")
            return True
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_response_model()
    if success:
        print("\n✅ Response模型测试通过！")
        print("📋 下一步可以开始设计推荐算法")
    else:
        print("\n❌ 测试失败，请检查Response模型实现")