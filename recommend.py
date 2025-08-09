# quick_recommend_test.py - 快速推荐测试
import requests
import time

BASE_URL = "http://localhost:8000"
proxies = {'http': None, 'https': None}

def quick_recommendation_test():
    """快速推荐生成测试"""
    print("⚡ 快速推荐生成测试")
    print("=" * 40)
    
    # 1. 创建用户
    timestamp = str(int(time.time()))[-6:]
    user_data = {
        "username": f"quick{timestamp}",
        "email": f"quick{timestamp}@example.com",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", 
                           json=user_data, proxies=proxies)
    
    if response.status_code != 201:
        print(f"❌ 注册失败: {response.text}")
        return
    
    token = response.json()['data']['token']
    headers = {"Authorization": f"Bearer {token}"}
    username = response.json()['data']['username']
    
    print(f"✅ 用户创建: {username}")
    
    # 2. 快速回答5个问题 - 使用确实存在的问题ID
    print("📝 获取可用问题...")
    
    # 先获取问题列表，确保使用存在的问题
    response = requests.get(f"{BASE_URL}/api/v1/questionnaire/questions", 
                          headers=headers, proxies=proxies)
    
    if response.status_code != 200:
        print("❌ 无法获取问题列表")
        return
    
    questions = response.json()['data']['questions']
    print(f"可用问题总数: {len(questions)}")
    
    # 从不同类别选择问题
    selected_answers = []
    categories_used = set()
    
    # 预定义一些答案选择 - 使用正确的答案值
    preferred_answers = {
        'skill_001': 'intermediate',
        'interest_001': 'web_frontend', 
        'goal_001': 'skill_upgrade',
        'style_001': 'hands_on',
        'time_001': '2_4h',  # 修正：使用正确的时间选项
        'time_002': 'steady_progress',
        'interest_002': 'visual_creative',
        'skill_002': 'intermediate',
        'skill_003': 'basic'
    }
    
    for question in questions:
        if len(selected_answers) >= 5:
            break
            
        q_id = question['question_id']
        category = question['category']
        
        # 避免同一类别重复太多
        if category not in categories_used or len(categories_used) < 3:
            if question['options']:
                # 尝试使用预定义的答案，否则使用第一个选项
                if q_id in preferred_answers:
                    # 检查预定义答案是否存在
                    valid_values = [opt['value'] for opt in question['options']]
                    if preferred_answers[q_id] in valid_values:
                        answer_value = preferred_answers[q_id]
                    else:
                        answer_value = question['options'][0]['value']
                else:
                    answer_value = question['options'][0]['value']
                
                selected_answers.append({
                    "question_id": q_id,
                    "answer_value": answer_value
                })
                categories_used.add(category)
    
    print(f"选择了 {len(selected_answers)} 个问题进行回答")
    print("提交答案...")
    
    for i, answer in enumerate(selected_answers, 1):
        response = requests.post(f"{BASE_URL}/api/v1/responses/submit", 
                               json=answer, headers=headers, proxies=proxies)
        
        if response.status_code == 200:
            result = response.json()
            progress = result['data']['progress']['progress_percentage']
            print(f"   {i}. {answer['question_id']} ✅ (进度: {progress}%)")
        else:
            print(f"   {i}. {answer['question_id']} ❌ - {response.text}")
            
    print(f"\n📊 最终统计: 回答了 {len(selected_answers)} 个问题，覆盖 {len(categories_used)} 个类别")
    
    # 3. 生成推荐
    print("\n🤖 生成推荐...")
    response = requests.post(f"{BASE_URL}/api/v1/recommendations/generate", 
                           headers=headers, proxies=proxies)
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        recommendation = response.json()['data']['recommendation']
        primary_path = recommendation['primary_path']
        
        print(f"🎯 推荐路径: {primary_path['name']}")
        print(f"⏱️ 学习时长: {primary_path.get('duration_weeks', 'N/A')} 周")
        print(f"📊 难度: {primary_path.get('difficulty', 'N/A')}")
        print(f"🎓 置信度: {recommendation.get('confidence_score', 'N/A')}")
        
        # 显示核心技术
        core_techs = primary_path.get('core_technologies', [])
        if core_techs:
            print(f"💻 核心技术: {', '.join(core_techs)}")
        
        # 显示学习阶段
        learning_plan = recommendation.get('learning_plan', {})
        stages = learning_plan.get('stages', [])
        if stages:
            print(f"📚 学习阶段数: {len(stages)}")
            print("阶段概览:")
            for i, stage in enumerate(stages[:3], 1):  # 只显示前3个阶段
                print(f"   {i}. {stage['name']} ({stage['duration_weeks']} 周)")
        
        print(f"\n✅ 推荐生成成功！")
        
        # 4. 验证推荐已保存
        print("\n💾 验证推荐保存...")
        response = requests.get(f"{BASE_URL}/api/v1/recommendations/my-recommendation", 
                              headers=headers, proxies=proxies)
        
        if response.status_code == 200:
            print("✅ 推荐已成功保存")
        else:
            print("❌ 推荐保存验证失败")
    
    else:
        result = response.json()
        print(f"❌ 推荐失败: {result.get('message', response.text)}")
    
    print("\n" + "=" * 40)
    return username

if __name__ == "__main__":
    username = quick_recommendation_test()
    if username:
        print(f"🎉 测试完成! 测试用户: {username}")