# complete_test_suite.py - ProgrammerRoadmap 完整测试套件
import requests
import json
import time
import random
import string
from datetime import datetime

BASE_URL = "http://localhost:8000"
PROXIES = {'http': None, 'https': None}

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
        self.start_time = time.time()
    
    def add_test(self, name, status, message=""):
        self.tests.append({"name": name, "status": status, "message": message})
        if status == "PASS":
            self.passed += 1
        else:
            self.failed += 1
        
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"   {status_icon} {name}: {message}")
    
    def summary(self):
        total = self.passed + self.failed
        duration = time.time() - self.start_time
        print(f"\n📊 测试总结:")
        print(f"   总计: {total} 个测试")
        print(f"   通过: {self.passed} 个 ✅")
        print(f"   失败: {self.failed} 个 ❌")
        print(f"   成功率: {(self.passed/total*100):.1f}%")
        print(f"   耗时: {duration:.2f} 秒")
        
        return self.failed == 0

class APITester:
    def __init__(self):
        self.results = TestResults()
        self.test_users = []
        self.tokens = {}
    
    def generate_test_user(self):
        """生成测试用户数据"""
        timestamp = str(int(time.time()))[-6:]
        random_suffix = ''.join(random.choices(string.digits, k=3))
        
        return {
            "username": f"test{timestamp}{random_suffix}",
            "email": f"test{timestamp}{random_suffix}@example.com",
            "password": "testpass123"
        }
    
    def test_server_connectivity(self):
        """测试服务器连接"""
        print("\n🔌 服务器连接测试")
        
        try:
            response = requests.get(f"{BASE_URL}/", proxies=PROXIES, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.results.add_test("服务器连接", "PASS", f"状态码: {response.status_code}")
                self.results.add_test("API信息", "PASS", f"版本: {data.get('version', 'N/A')}")
            else:
                self.results.add_test("服务器连接", "FAIL", f"状态码: {response.status_code}")
        except Exception as e:
            self.results.add_test("服务器连接", "FAIL", str(e))
    
    def test_health_check(self):
        """测试健康检查"""
        print("\n🏥 健康检查测试")
        
        try:
            response = requests.get(f"{BASE_URL}/health", proxies=PROXIES, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.results.add_test("健康检查端点", "PASS", f"状态: {data.get('status', 'N/A')}")
                
                # 检查数据库状态
                db_status = data.get('database', {}).get('status', 'unknown')
                if db_status == 'connected':
                    self.results.add_test("数据库连接", "PASS", f"状态: {db_status}")
                else:
                    self.results.add_test("数据库连接", "FAIL", f"状态: {db_status}")
            else:
                self.results.add_test("健康检查端点", "FAIL", f"状态码: {response.status_code}")
        except Exception as e:
            self.results.add_test("健康检查端点", "FAIL", str(e))
    
    def test_user_registration(self):
        """测试用户注册"""
        print("\n👤 用户注册测试")
        
        # 测试正常注册
        user_data = self.generate_test_user()
        try:
            response = requests.post(f"{BASE_URL}/api/v1/auth/register", 
                                   json=user_data, proxies=PROXIES)
            
            if response.status_code == 201:
                data = response.json()
                user_id = data['data']['user_id']
                token = data['data']['token']
                
                self.test_users.append(user_id)
                self.tokens[user_id] = token
                
                self.results.add_test("用户注册", "PASS", f"用户ID: {user_id}")
                self.results.add_test("JWT Token生成", "PASS", f"Token长度: {len(token)}")
            else:
                self.results.add_test("用户注册", "FAIL", f"状态码: {response.status_code}")
        except Exception as e:
            self.results.add_test("用户注册", "FAIL", str(e))
        
        # 测试重复注册
        try:
            response = requests.post(f"{BASE_URL}/api/v1/auth/register", 
                                   json=user_data, proxies=PROXIES)
            
            if response.status_code == 400:
                self.results.add_test("重复注册验证", "PASS", "正确拒绝重复用户名")
            else:
                self.results.add_test("重复注册验证", "FAIL", f"状态码: {response.status_code}")
        except Exception as e:
            self.results.add_test("重复注册验证", "FAIL", str(e))
        
        # 测试无效数据
        invalid_cases = [
            {"username": "", "email": "test@example.com", "password": "123456"},
            {"username": "test", "email": "invalid-email", "password": "123456"},
            {"username": "test", "email": "test@example.com", "password": "123"}
        ]
        
        for i, invalid_data in enumerate(invalid_cases, 1):
            try:
                response = requests.post(f"{BASE_URL}/api/v1/auth/register", 
                                       json=invalid_data, proxies=PROXIES)
                
                if response.status_code == 400:
                    self.results.add_test(f"无效数据验证-{i}", "PASS", "正确拒绝无效数据")
                else:
                    self.results.add_test(f"无效数据验证-{i}", "FAIL", f"状态码: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"无效数据验证-{i}", "FAIL", str(e))
    
    def test_user_authentication(self):
        """测试用户认证"""
        print("\n🔐 用户认证测试")
        
        if not self.test_users:
            self.results.add_test("用户认证", "FAIL", "没有可测试的用户")
            return
        
        user_id = self.test_users[0]
        token = self.tokens[user_id]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 测试获取用户资料
        try:
            response = requests.get(f"{BASE_URL}/api/v1/auth/profile", 
                                  headers=headers, proxies=PROXIES)
            
            if response.status_code == 200:
                data = response.json()
                self.results.add_test("获取用户资料", "PASS", f"用户: {data['data']['username']}")
            else:
                self.results.add_test("获取用户资料", "FAIL", f"状态码: {response.status_code}")
        except Exception as e:
            self.results.add_test("获取用户资料", "FAIL", str(e))
        
        # 测试无效Token
        try:
            invalid_headers = {"Authorization": "Bearer invalid_token"}
            response = requests.get(f"{BASE_URL}/api/v1/auth/profile", 
                                  headers=invalid_headers, proxies=PROXIES)
            
            if response.status_code == 401:
                self.results.add_test("无效Token验证", "PASS", "正确拒绝无效Token")
            else:
                self.results.add_test("无效Token验证", "FAIL", f"状态码: {response.status_code}")
        except Exception as e:
            self.results.add_test("无效Token验证", "FAIL", str(e))
    
    def test_questionnaire_system(self):
        """测试问卷系统"""
        print("\n📝 问卷系统测试")
        
        # 测试获取问题列表
        try:
            response = requests.get(f"{BASE_URL}/api/v1/questionnaire/questions", 
                                  proxies=PROXIES)
            
            if response.status_code == 200:
                data = response.json()
                questions = data['data']['questions']
                self.results.add_test("获取问题列表", "PASS", f"问题数量: {len(questions)}")
                
                # 验证问题结构
                if questions and all(key in questions[0] for key in ['question_id', 'question_text', 'options']):
                    self.results.add_test("问题数据结构", "PASS", "问题格式正确")
                else:
                    self.results.add_test("问题数据结构", "FAIL", "问题格式不完整")
            else:
                self.results.add_test("获取问题列表", "FAIL", f"状态码: {response.status_code}")
        except Exception as e:
            self.results.add_test("获取问题列表", "FAIL", str(e))
        
        # 测试获取问题分类
        try:
            response = requests.get(f"{BASE_URL}/api/v1/questionnaire/categories", 
                                  proxies=PROXIES)
            
            if response.status_code == 200:
                data = response.json()
                categories = data['data']['categories']
                self.results.add_test("获取问题分类", "PASS", f"分类数量: {len(categories)}")
            else:
                self.results.add_test("获取问题分类", "FAIL", f"状态码: {response.status_code}")
        except Exception as e:
            self.results.add_test("获取问题分类", "FAIL", str(e))
    
    def test_response_submission(self):
        """测试答案提交"""
        print("\n📤 答案提交测试")
        
        if not self.test_users:
            self.results.add_test("答案提交", "FAIL", "没有可测试的用户")
            return
        
        user_id = self.test_users[0]
        token = self.tokens[user_id]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 获取问题列表用于测试
        try:
            response = requests.get(f"{BASE_URL}/api/v1/questionnaire/questions", 
                                  headers=headers, proxies=PROXIES)
            
            if response.status_code != 200:
                self.results.add_test("获取测试问题", "FAIL", "无法获取问题列表")
                return
            
            questions = response.json()['data']['questions']
            
            # 测试提交答案
            test_count = 0
            for question in questions[:5]:  # 测试前5个问题
                if question['options']:
                    answer_data = {
                        "question_id": question['question_id'],
                        "answer_value": question['options'][0]['value']
                    }
                    
                    try:
                        response = requests.post(f"{BASE_URL}/api/v1/responses/submit", 
                                               json=answer_data, headers=headers, proxies=PROXIES)
                        
                        if response.status_code == 200:
                            data = response.json()
                            progress = data['data']['progress']['progress_percentage']
                            self.results.add_test(f"提交答案-{question['question_id']}", "PASS", 
                                                f"进度: {progress}%")
                            test_count += 1
                        else:
                            self.results.add_test(f"提交答案-{question['question_id']}", "FAIL", 
                                                f"状态码: {response.status_code}")
                    except Exception as e:
                        self.results.add_test(f"提交答案-{question['question_id']}", "FAIL", str(e))
            
            # 测试获取用户答案
            try:
                response = requests.get(f"{BASE_URL}/api/v1/responses/my-answers", 
                                      headers=headers, proxies=PROXIES)
                
                if response.status_code == 200:
                    data = response.json()
                    count = data['data']['count']
                    self.results.add_test("获取用户答案", "PASS", f"答案数量: {count}")
                else:
                    self.results.add_test("获取用户答案", "FAIL", f"状态码: {response.status_code}")
            except Exception as e:
                self.results.add_test("获取用户答案", "FAIL", str(e))
                
        except Exception as e:
            self.results.add_test("答案提交测试", "FAIL", str(e))
    
    def test_recommendation_system(self):
        """测试推荐系统"""
        print("\n🎯 推荐系统测试")
        
        # 创建专门用于推荐测试的用户
        user_data = self.generate_test_user()
        try:
            response = requests.post(f"{BASE_URL}/api/v1/auth/register", 
                                   json=user_data, proxies=PROXIES)
            
            if response.status_code != 201:
                self.results.add_test("推荐测试用户创建", "FAIL", "无法创建测试用户")
                return
            
            token = response.json()['data']['token']
            headers = {"Authorization": f"Bearer {token}"}
            
            # 获取问题并提交足够的答案
            response = requests.get(f"{BASE_URL}/api/v1/questionnaire/questions", 
                                  headers=headers, proxies=PROXIES)
            
            if response.status_code != 200:
                self.results.add_test("获取推荐测试问题", "FAIL", "无法获取问题")
                return
            
            questions = response.json()['data']['questions']
            
            # 提交至少5个答案
            submitted = 0
            for question in questions:
                if submitted >= 5:
                    break
                
                if question['options']:
                    answer_data = {
                        "question_id": question['question_id'],
                        "answer_value": question['options'][0]['value']
                    }
                    
                    response = requests.post(f"{BASE_URL}/api/v1/responses/submit", 
                                           json=answer_data, headers=headers, proxies=PROXIES)
                    
                    if response.status_code == 200:
                        submitted += 1
            
            if submitted < 5:
                self.results.add_test("推荐答案准备", "FAIL", f"只提交了{submitted}个答案")
                return
            
            self.results.add_test("推荐答案准备", "PASS", f"成功提交{submitted}个答案")
            
            # 测试生成推荐
            try:
                response = requests.post(f"{BASE_URL}/api/v1/recommendations/generate", 
                                       headers=headers, proxies=PROXIES)
                
                if response.status_code == 200:
                    data = response.json()
                    recommendation = data['data']['recommendation']
                    primary_path = recommendation['primary_path']
                    
                    self.results.add_test("生成推荐", "PASS", f"路径: {primary_path['name']}")
                    self.results.add_test("推荐置信度", "PASS", 
                                        f"置信度: {data['data']['confidence_score']}")
                    
                    # 验证推荐数据结构
                    required_fields = ['primary_path', 'learning_plan', 'confidence_score']
                    if all(field in recommendation for field in required_fields):
                        self.results.add_test("推荐数据结构", "PASS", "包含所有必需字段")
                    else:
                        self.results.add_test("推荐数据结构", "FAIL", "缺少必需字段")
                        
                else:
                    self.results.add_test("生成推荐", "FAIL", f"状态码: {response.status_code}")
                    return
            except Exception as e:
                self.results.add_test("生成推荐", "FAIL", str(e))
                return
            
            # 测试获取推荐
            try:
                response = requests.get(f"{BASE_URL}/api/v1/recommendations/my-recommendation", 
                                      headers=headers, proxies=PROXIES)
                
                if response.status_code == 200:
                    self.results.add_test("获取推荐", "PASS", "成功获取保存的推荐")
                else:
                    self.results.add_test("获取推荐", "FAIL", f"状态码: {response.status_code}")
            except Exception as e:
                self.results.add_test("获取推荐", "FAIL", str(e))
                
        except Exception as e:
            self.results.add_test("推荐系统测试", "FAIL", str(e))
    
    def test_learning_paths(self):
        """测试学习路径"""
        print("\n📚 学习路径测试")
        
        try:
            response = requests.get(f"{BASE_URL}/api/v1/recommendations/learning-paths", 
                                  proxies=PROXIES)
            
            if response.status_code == 200:
                data = response.json()
                paths = data['data']['paths']
                
                self.results.add_test("获取学习路径", "PASS", f"路径数量: {len(paths)}")
                
                # 验证路径结构
                expected_paths = ['frontend', 'backend', 'mobile', 'data_science']
                for path_name in expected_paths:
                    if path_name in paths:
                        path_info = paths[path_name]
                        required_fields = ['name', 'description', 'duration_weeks']
                        if all(field in path_info for field in required_fields):
                            self.results.add_test(f"路径结构-{path_name}", "PASS", 
                                                f"名称: {path_info['name']}")
                        else:
                            self.results.add_test(f"路径结构-{path_name}", "FAIL", "缺少必需字段")
                    else:
                        self.results.add_test(f"路径存在-{path_name}", "FAIL", "路径不存在")
                        
            else:
                self.results.add_test("获取学习路径", "FAIL", f"状态码: {response.status_code}")
        except Exception as e:
            self.results.add_test("获取学习路径", "FAIL", str(e))
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n🚨 错误处理测试")
        
        # 测试404错误
        try:
            response = requests.get(f"{BASE_URL}/api/v1/nonexistent", proxies=PROXIES)
            if response.status_code == 404:
                self.results.add_test("404错误处理", "PASS", "正确返回404")
            else:
                self.results.add_test("404错误处理", "FAIL", f"状态码: {response.status_code}")
        except Exception as e:
            self.results.add_test("404错误处理", "FAIL", str(e))
        
        # 测试无认证访问受保护端点
        try:
            response = requests.get(f"{BASE_URL}/api/v1/auth/profile", proxies=PROXIES)
            if response.status_code == 401:
                self.results.add_test("401认证错误", "PASS", "正确拒绝无认证访问")
            else:
                self.results.add_test("401认证错误", "FAIL", f"状态码: {response.status_code}")
        except Exception as e:
            self.results.add_test("401认证错误", "FAIL", str(e))
    
    def test_data_consistency(self):
        """测试数据一致性"""
        print("\n🔄 数据一致性测试")
        
        if not self.test_users:
            self.results.add_test("数据一致性", "FAIL", "没有可测试的用户")
            return
        
        user_id = self.test_users[0]
        token = self.tokens[user_id]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 测试问卷状态一致性
        try:
            # 获取问卷状态
            response = requests.get(f"{BASE_URL}/api/v1/questionnaire/status", 
                                  headers=headers, proxies=PROXIES)
            
            if response.status_code == 200:
                status_data = response.json()['data']
                overall = status_data['overall_progress']
                
                # 获取用户答案
                response = requests.get(f"{BASE_URL}/api/v1/responses/my-answers", 
                                      headers=headers, proxies=PROXIES)
                
                if response.status_code == 200:
                    answers_data = response.json()['data']
                    actual_count = answers_data['count']
                    
                    # 验证计数一致性
                    expected_field = 'answered_count'  # 修正字段名
                    if expected_field in overall:
                        if overall[expected_field] == actual_count:
                            self.results.add_test("答案计数一致性", "PASS", 
                                                f"计数匹配: {actual_count}")
                        else:
                            self.results.add_test("答案计数一致性", "FAIL", 
                                                f"状态显示{overall[expected_field]}，实际{actual_count}")
                    else:
                        # 尝试其他可能的字段名
                        possible_fields = ['answered_questions', 'answered_count', 'count']
                        found_field = None
                        for field in possible_fields:
                            if field in overall:
                                found_field = field
                                break
                        
                        if found_field:
                            if overall[found_field] == actual_count:
                                self.results.add_test("答案计数一致性", "PASS", 
                                                    f"计数匹配: {actual_count} (字段: {found_field})")
                            else:
                                self.results.add_test("答案计数一致性", "FAIL", 
                                                    f"状态显示{overall[found_field]}，实际{actual_count} (字段: {found_field})")
                        else:
                            self.results.add_test("答案计数一致性", "FAIL", 
                                                f"找不到计数字段，overall_progress包含: {list(overall.keys())}")
                else:
                    self.results.add_test("答案计数一致性", "FAIL", "无法获取用户答案")
            else:
                self.results.add_test("问卷状态获取", "FAIL", f"状态码: {response.status_code}")
        except Exception as e:
            self.results.add_test("数据一致性测试", "FAIL", str(e))
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 ProgrammerRoadmap API 完整测试套件")
        print("=" * 60)
        print(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试目标: {BASE_URL}")
        
        # 运行所有测试模块
        self.test_server_connectivity()
        self.test_health_check()
        self.test_user_registration()
        self.test_user_authentication()
        self.test_questionnaire_system()
        self.test_response_submission()
        self.test_recommendation_system()
        self.test_learning_paths()
        self.test_error_handling()
        self.test_data_consistency()
        
        # 输出测试结果
        print("\n" + "=" * 60)
        success = self.results.summary()
        
        if success:
            print("\n🎉 所有测试通过！系统运行完美！")
            print("✅ ProgrammerRoadmap API 已准备就绪")
        else:
            print("\n⚠️ 部分测试失败，请检查上述错误")
            print("❌ 系统可能存在问题")
        
        return success

def main():
    """主函数"""
    print("正在连接到API服务器...")
    
    # 检查服务器是否运行
    try:
        response = requests.get(f"{BASE_URL}/", proxies=PROXIES, timeout=5)
        if response.status_code != 200:
            print(f"❌ 服务器响应异常: {response.status_code}")
            print("请确保API服务器正在运行: python run.py")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器")
        print("请确保API服务器正在运行: python run.py")
        return False
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False
    
    # 运行测试套件
    tester = APITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)