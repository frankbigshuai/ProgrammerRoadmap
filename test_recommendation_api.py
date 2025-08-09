# test_recommendation_api.py
"""
推荐系统API测试示例
"""
import requests
import json
BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_complete_flow():
    """测试完整的推荐流程"""
    
    print("🧪 开始测试推荐系统...")
    
    # 1. 注册测试用户
    print("\n1️⃣ 注册测试用户...")
    import time
    timestamp = int(time.time())
    register_data = {
    "username": f"test_user_{timestamp}",
    "email": f"test_{timestamp}@example.com",
    "password": "123456"
}
    
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    if response.status_code == 201:
        user_data = response.json()['data']
        token = user_data['token']
        print(f"✅ 用户注册成功: {user_data['username']}")
    else:
        print(f"❌ 注册失败: {response.json()}")
        return
    
    # 设置认证头
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. 获取问卷题目
    print("\n2️⃣ 获取问卷题目...")
    response = requests.get(f"{BASE_URL}/questionnaire/questions", headers=headers)
    if response.status_code == 200:
        questions = response.json()['data']['questions']
        print(f"✅ 获取到 {len(questions)} 个问题")
    else:
        print(f"❌ 获取问题失败: {response.json()}")
        return
    
    # 3. 提交测试答案
    print("\n3️⃣ 提交测试答案...")
    test_answers = [
        {"question_id": "skill_01", "answer_value": "intermediate"},
        {"question_id": "skill_02", "answer_value": "python"},
        {"question_id": "interest_01", "answer_value": "data_analysis"},
        {"question_id": "interest_02", "answer_value": "logical"},
        {"question_id": "career_01", "answer_value": "specialist"},
        {"question_id": "learning_01", "answer_value": "hands_on"},
        {"question_id": "time_01", "answer_value": "dedicated"}
    ]
    
    # 批量提交答案
    response = requests.post(f"{BASE_URL}/responses/batch", 
                           json={"answers": test_answers}, 
                           headers=headers)
    if response.status_code == 200:
        result = response.json()['data']
        print(f"✅ 提交答案成功: {result['success_count']}/{result['total_count']}")
    else:
        print(f"❌ 提交答案失败: {response.json()}")
        return
    
    # 4. 生成推荐
    print("\n4️⃣ 生成个性化推荐...")
    response = requests.post(f"{BASE_URL}/recommendations/generate", headers=headers)
    if response.status_code == 200:
        recommendation = response.json()['data']['recommendation']
        print(f"✅ 推荐生成成功!")
        print(f"   主要路径: {recommendation['primary_path']['name']}")
        print(f"   置信度: {recommendation['confidence_score']}")
        print(f"   学习时长: {recommendation['learning_plan']['total_duration_weeks']} 周")
    else:
        print(f"❌ 推荐生成失败: {response.json()}")
        return
    
    # 5. 获取学习路径详情
    print("\n5️⃣ 获取学习路径详情...")
    primary_path_name = recommendation['primary_path']['path_name']
    response = requests.get(f"{BASE_URL}/recommendations/path-details/{primary_path_name}")
    if response.status_code == 200:
        path_details = response.json()['data']['path']
        print(f"✅ 路径详情获取成功: {path_details['name']}")
        print(f"   难度等级: {path_details['difficulty']}")
        print(f"   核心技术: {', '.join(path_details['core_technologies'])}")
    else:
        print(f"❌ 获取路径详情失败: {response.json()}")
    
    # 6. 获取已保存的推荐
    print("\n6️⃣ 获取已保存的推荐...")
    response = requests.get(f"{BASE_URL}/recommendations/my-recommendation", headers=headers)
    if response.status_code == 200:
        saved_recommendation = response.json()['data']['recommendation']
        print(f"✅ 获取已保存推荐成功!")
        print(f"   是否为缓存结果: {response.json()['data']['is_cached']}")
    else:
        print(f"❌ 获取保存推荐失败: {response.json()}")
    
    # 7. 提交反馈
    print("\n7️⃣ 提交推荐反馈...")
    feedback_data = {
        "rating": 4,
        "feedback": "推荐很准确，符合我的兴趣和技能水平",
        "is_helpful": True,
        "suggestions": ["希望能提供更多具体的学习资源"]
    }
    response = requests.post(f"{BASE_URL}/recommendations/feedback", 
                           json=feedback_data, headers=headers)
    if response.status_code == 200:
        print(f"✅ 反馈提交成功!")
    else:
        print(f"❌ 反馈提交失败: {response.json()}")
    
    print(f"\n🎉 推荐系统测试完成！")

def test_get_all_paths():
    """测试获取所有学习路径"""
    print("\n📋 获取所有可用学习路径...")
    response = requests.get(f"{BASE_URL}/recommendations/learning-paths")
    if response.status_code == 200:
        paths = response.json()['data']['paths']
        print(f"✅ 获取到 {len(paths)} 个学习路径:")
        for path_key, path_info in paths.items():
            print(f"   • {path_info['name']}: {path_info['description']}")
    else:
        print(f"❌ 获取学习路径失败: {response.json()}")

def display_recommendation_details(recommendation):
    """详细显示推荐结果"""
    print(f"\n📊 推荐详情:")
    print(f"=" * 50)
    
    # 主路径信息
    primary_path = recommendation['primary_path']
    print(f"🎯 推荐路径: {primary_path['name']}")
    print(f"📝 描述: {primary_path['description']}")
    print(f"⏱️ 预计时长: {primary_path.get('duration_weeks', 'N/A')} 周")
    print(f"📈 难度等级: {primary_path.get('difficulty', 'N/A')}")
    
    # 路径匹配分数
    if 'path_scores' in recommendation:
        print(f"\n📊 各路径匹配度:")
        for path, score in recommendation['path_scores'].items():
            print(f"   {path}: {score:.2f}")
    
    # 学习计划
    learning_plan = recommendation.get('learning_plan', {})
    if learning_plan:
        print(f"\n📚 学习计划:")
        stages = learning_plan.get('stages', [])
        for i, stage in enumerate(stages, 1):
            print(f"   阶段 {i}: {stage['name']} ({stage['duration_weeks']} 周)")
            skills = stage.get('skills', [])
            for skill in skills[:3]:  # 只显示前3个技能
                print(f"     • {skill['name']} (优先级: {skill['priority']})")
    
    # 补充技能
    supplementary = recommendation.get('supplementary_skills', [])
    if supplementary:
        print(f"\n🎁 推荐补充技能:")
        for skill in supplementary:
            print(f"   • {skill['name']}: {skill['reason']}")
    
    print(f"\n✨ 推荐置信度: {recommendation.get('confidence_score', 0)}")

if __name__ == "__main__":
    # 测试获取所有路径（不需要认证）
    test_get_all_paths()
    
    # 测试完整流程
    test_complete_flow()