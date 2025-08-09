# full_recommendation_test.py - 完整推荐流程测试
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_full_recommendation_flow():
    """测试完整的推荐生成流程"""
    print("🎯 完整推荐流程测试")
    print("=" * 50)
    
    proxies = {'http': None, 'https': None}
    
    # 1. 用户注册
    print("1️⃣ 创建测试用户...")
    timestamp = int(time.time())
    user_data = {
        "username": f"recommend_test_{timestamp}",
        "email": f"recommend_test_{timestamp}@example.com",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", 
                           json=user_data, proxies=proxies)
    
    if response.status_code != 201:
        print(f"❌ 注册失败: {response.text}")
        return
    
    user_info = response.json()
    token = user_info['data']['token']
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"✅ 用户创建成功: {user_info['data']['username']}")
    
    # 2. 回答足够的问题（至少5个）
    print("\n2️⃣ 回答问题以满足推荐条件...")
    
    # 获取可用的问题
    response = requests.get(f"{BASE_URL}/api/v1/questionnaire/questions", 
                          headers=headers, proxies=proxies)
    questions = response.json()['data']['questions']
    
    # 选择不同类别的问题进行回答
    answers_to_submit = []
    categories_answered = set()
    
    for question in questions:
        if len(answers_to_submit) >= 7:  # 回答7个问题，超过最小要求
            break
            
        category = question['category']
        if category not in categories_answered:
            # 为每个类别选择第一个可用的答案
            if question['options']:
                first_option = question['options'][0]
                answers_to_submit.append({
                    "question_id": question['question_id'],
                    "answer_value": first_option['value']
                })
                categories_answered.add(category)
    
    print(f"准备回答 {len(answers_to_submit)} 个问题，覆盖 {len(categories_answered)} 个类别")
    
    # 提交答案
    for i, answer in enumerate(answers_to_submit, 1):
        response = requests.post(f"{BASE_URL}/api/v1/responses/submit", 
                               json=answer, headers=headers, proxies=proxies)
        
        if response.status_code == 200:
            result = response.json()
            progress = result['data']['progress']
            print(f"   ✅ 问题 {i}: {answer['question_id']} (进度: {progress['progress_percentage']}%)")
        else:
            print(f"   ❌ 问题 {i}: {answer['question_id']} 失败")
    
    # 3. 检查答题进度
    print("\n3️⃣ 检查答题进度...")
    response = requests.get(f"{BASE_URL}/api/v1/responses/my-answers", 
                          headers=headers, proxies=proxies)
    
    if response.status_code == 200:
        answers = response.json()
        answered_count = answers['data']['count']
        print(f"✅ 已回答 {answered_count} 个问题")
        
        if answered_count >= 5:
            print("🎯 满足推荐生成条件！")
        else:
            print(f"⚠️ 还需要回答 {5 - answered_count} 个问题")
            return
    
    # 4. 生成推荐
    print("\n4️⃣ 生成个性化推荐...")
    response = requests.post(f"{BASE_URL}/api/v1/recommendations/generate", 
                           headers=headers, proxies=proxies)
    
    print(f"推荐生成状态码: {response.status_code}")
    
    if response.status_code == 200:
        recommendation = response.json()
        data = recommendation['data']
        primary_path = data['recommendation']['primary_path']
        
        print(f"✅ 推荐生成成功!")
        print(f"   🎯 推荐路径: {primary_path['name']}")
        print(f"   ⏱️ 学习时长: {primary_path.get('duration_weeks', 'N/A')} 周")
        print(f"   📊 置信度: {data['confidence_score']}")
        print(f"   🎓 难度级别: {primary_path.get('difficulty', 'N/A')}")
        
        # 显示学习计划概览
        learning_plan = data['recommendation']['learning_plan']
        if learning_plan and 'stages' in learning_plan:
            print(f"   📚 学习阶段: {len(learning_plan['stages'])} 个")
        
        # 显示补充技能
        supplementary = data['recommendation'].get('supplementary_skills', [])
        if supplementary:
            print(f"   🔧 补充技能: {len(supplementary)} 项")
    else:
        result = response.json()
        print(f"❌ 推荐生成失败: {result.get('message', response.text)}")
        return
    
    # 5. 获取推荐结果
    print("\n5️⃣ 获取保存的推荐...")
    response = requests.get(f"{BASE_URL}/api/v1/recommendations/my-recommendation", 
                          headers=headers, proxies=proxies)
    
    if response.status_code == 200:
        print("✅ 成功获取保存的推荐结果")
    else:
        print(f"❌ 获取推荐失败: {response.text}")
    
    # 6. 获取问卷状态
    print("\n6️⃣ 检查问卷完成状态...")
    response = requests.get(f"{BASE_URL}/api/v1/questionnaire/status", 
                          headers=headers, proxies=proxies)
    
    if response.status_code == 200:
        status = response.json()
        overall = status['data']['overall_progress']
        print(f"✅ 问卷状态: {overall['progress_percentage']}% 完成")
        print(f"   回答数量: {overall['answered_questions']}/{overall['total_questions']}")
        print(f"   是否完成: {overall['is_completed']}")
    
    print("\n" + "=" * 50)
    print("🎉 完整推荐流程测试完成!")

if __name__ == "__main__":
    test_full_recommendation_flow()