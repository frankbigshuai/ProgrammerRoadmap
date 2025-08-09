# app/services/recommendation_engine.py
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

class RecommendationEngine:
    """程序员学习路径推荐引擎"""
    
    def __init__(self):
        """初始化推荐引擎"""
        self.learning_paths = self._init_learning_paths()
        self.skill_weights = {
            'frontend': 1.0,
            'backend': 1.0,
            'mobile': 1.0,
            'data_science': 1.0
        }
    
    def generate_recommendation(self, user_data: Dict) -> Dict:
        """
        根据用户问卷数据生成个性化推荐
        
        Args:
            user_data: 从Response.get_responses_for_recommendation()获取的数据
            
        Returns:
            包含推荐路径、学习计划和资源的字典
        """
        try:
            # 1. 分析用户能力和兴趣
            user_profile = self._analyze_user_profile(user_data)
            
            # 2. 计算路径匹配度
            path_scores = self._calculate_path_scores(user_profile)
            
            # 3. 选择最适合的主路径
            primary_path = self._select_primary_path(path_scores, user_profile)
            
            # 4. 生成学习计划
            learning_plan = self._create_learning_plan(primary_path, user_profile)
            
            # 5. 推荐补充技能
            supplementary_skills = self._recommend_supplementary_skills(primary_path, user_profile)
            
            # 6. 生成完整推荐结果
            recommendation = {
                'user_id': user_data.get('user_id'),
                'generated_at': datetime.utcnow().isoformat(),
                'user_profile': user_profile,
                'primary_path': primary_path,
                'path_scores': path_scores,
                'learning_plan': learning_plan,
                'supplementary_skills': supplementary_skills,
                'confidence_score': self._calculate_confidence_score(user_data, path_scores)
            }
            
            print(f"✅ 为用户 {user_data.get('user_id')} 生成推荐成功")
            return recommendation
            
        except Exception as e:
            print(f"❌ 推荐生成失败: {e}")
            return self._get_default_recommendation(user_data.get('user_id'))
    
    def _analyze_user_profile(self, user_data: Dict) -> Dict:
        """分析用户画像"""
        profile = {
            'skill_levels': {},
            'interests': {},
            'goals': [],
            'learning_preferences': {},
            'time_availability': {},
            'experience_level': 'beginner'
        }
        
        # 技能水平分析
        skill_assessment = user_data.get('skill_assessment', {})
        for path, skills in skill_assessment.items():
            if isinstance(skills, dict):
                level = skills.get('level', 0)
                foundation = skills.get('foundation', 0)
                profile['skill_levels'][path] = {
                    'level': level,
                    'foundation': foundation,
                    'combined_score': (level * 0.6 + foundation * 0.4)
                }
        
        # 兴趣偏好分析
        interest_data = user_data.get('interest_preference', {})
        if isinstance(interest_data, dict):
            profile['interests'] = interest_data
        
        # 职业目标分析
        career_goals = user_data.get('career_goal', {}).get('goals', [])
        profile['goals'] = career_goals
        
        # 学习方式偏好
        learning_styles = user_data.get('learning_style', {}).get('styles', [])
        profile['learning_preferences'] = self._process_learning_styles(learning_styles)
        
        # 时间规划
        time_plans = user_data.get('time_planning', {}).get('plans', [])
        profile['time_availability'] = self._process_time_planning(time_plans)
        
        # 确定经验水平
        profile['experience_level'] = self._determine_experience_level(profile['skill_levels'])
        
        return profile
    
    def _calculate_path_scores(self, user_profile: Dict) -> Dict:
        """计算各路径的匹配度分数"""
        path_scores = {}
        
        for path in ['frontend', 'backend', 'mobile', 'data_science']:
            score = 0.0
            
            # 1. 技能基础分数 (30%)
            skill_data = user_profile['skill_levels'].get(path, {})
            skill_score = skill_data.get('combined_score', 0)
            score += skill_score * 0.3
            
            # 2. 兴趣匹配分数 (40%)
            interest_score = user_profile['interests'].get(path, 0)
            score += interest_score * 0.4
            
            # 3. 目标匹配分数 (20%)
            goal_score = self._calculate_goal_match(path, user_profile['goals'])
            score += goal_score * 0.2
            
            # 4. 学习方式匹配 (10%)
            learning_match = self._calculate_learning_match(path, user_profile['learning_preferences'])
            score += learning_match * 0.1
            
            path_scores[path] = min(1.0, score)
        
        return path_scores
    
    def _select_primary_path(self, path_scores: Dict, user_profile: Dict) -> Dict:
        """选择主要学习路径"""
        # 找到得分最高的路径
        best_path = max(path_scores, key=path_scores.get)
        best_score = path_scores[best_path]
        
        # 获取路径详细信息
        path_info = self.learning_paths[best_path].copy()
        path_info['score'] = best_score
        path_info['path_name'] = best_path
        
        return path_info
    
    def _create_learning_plan(self, primary_path: Dict, user_profile: Dict) -> Dict:
        """创建学习计划"""
        experience_level = user_profile['experience_level']
        time_availability = user_profile['time_availability']
        
        # 根据经验水平调整学习阶段
        stages = primary_path['stages'].copy()
        
        # 根据时间可用性调整时间线
        timeline_multiplier = self._get_timeline_multiplier(time_availability)
        
        learning_plan = {
            'path_name': primary_path['path_name'],
            'total_duration_weeks': int(primary_path['duration_weeks'] * timeline_multiplier),
            'difficulty_level': primary_path['difficulty'],
            'stages': []
        }
        
        # 处理每个学习阶段
        for stage in stages:
            adjusted_stage = stage.copy()
            adjusted_stage['duration_weeks'] = int(stage['duration_weeks'] * timeline_multiplier)
            
            # 根据用户基础调整技能点
            if experience_level == 'beginner':
                adjusted_stage['skills'] = stage['skills']
            elif experience_level == 'intermediate':
                # 中级用户可以跳过一些基础技能
                adjusted_stage['skills'] = [s for s in stage['skills'] if s.get('level', 1) > 1]
            
            learning_plan['stages'].append(adjusted_stage)
        
        return learning_plan
    
    def _init_learning_paths(self) -> Dict:
        """初始化学习路径模板"""
        return {
            'frontend': {
                'name': '前端开发',
                'description': '专注于用户界面和用户体验的Web开发',
                'duration_weeks': 24,
                'difficulty': 'beginner',
                'core_technologies': ['HTML', 'CSS', 'JavaScript', 'React', 'Vue'],
                'stages': [
                    {
                        'name': '基础阶段',
                        'duration_weeks': 8,
                        'skills': [
                            {'name': 'HTML5', 'level': 1, 'priority': 'high'},
                            {'name': 'CSS3', 'level': 1, 'priority': 'high'},
                            {'name': 'JavaScript基础', 'level': 1, 'priority': 'high'},
                            {'name': 'DOM操作', 'level': 1, 'priority': 'medium'}
                        ]
                    },
                    {
                        'name': '进阶阶段',
                        'duration_weeks': 10,
                        'skills': [
                            {'name': 'React/Vue框架', 'level': 2, 'priority': 'high'},
                            {'name': '状态管理', 'level': 2, 'priority': 'medium'},
                            {'name': '前端工程化', 'level': 2, 'priority': 'medium'},
                            {'name': 'API调用', 'level': 2, 'priority': 'high'}
                        ]
                    },
                    {
                        'name': '高级阶段',
                        'duration_weeks': 6,
                        'skills': [
                            {'name': '性能优化', 'level': 3, 'priority': 'medium'},
                            {'name': '测试框架', 'level': 3, 'priority': 'low'},
                            {'name': '微前端', 'level': 3, 'priority': 'low'}
                        ]
                    }
                ]
            },
            'backend': {
                'name': '后端开发',
                'description': '专注于服务器端逻辑、数据库和API开发',
                'duration_weeks': 26,
                'difficulty': 'intermediate',
                'core_technologies': ['Python', 'Node.js', 'Database', 'API', 'Cloud'],
                'stages': [
                    {
                        'name': '基础阶段',
                        'duration_weeks': 10,
                        'skills': [
                            {'name': 'Python/Java/Node.js', 'level': 1, 'priority': 'high'},
                            {'name': '数据库基础', 'level': 1, 'priority': 'high'},
                            {'name': 'HTTP协议', 'level': 1, 'priority': 'medium'},
                            {'name': 'RESTful API', 'level': 1, 'priority': 'high'}
                        ]
                    },
                    {
                        'name': '进阶阶段',
                        'duration_weeks': 12,
                        'skills': [
                            {'name': '框架开发', 'level': 2, 'priority': 'high'},
                            {'name': '数据库设计', 'level': 2, 'priority': 'high'},
                            {'name': '缓存技术', 'level': 2, 'priority': 'medium'},
                            {'name': '消息队列', 'level': 2, 'priority': 'medium'}
                        ]
                    },
                    {
                        'name': '高级阶段',
                        'duration_weeks': 4,
                        'skills': [
                            {'name': '微服务架构', 'level': 3, 'priority': 'medium'},
                            {'name': '容器化部署', 'level': 3, 'priority': 'medium'},
                            {'name': '性能优化', 'level': 3, 'priority': 'low'}
                        ]
                    }
                ]
            },
            'mobile': {
                'name': '移动开发',
                'description': '专注于iOS和Android移动应用开发',
                'duration_weeks': 28,
                'difficulty': 'intermediate',
                'core_technologies': ['React Native', 'Flutter', 'Swift', 'Kotlin'],
                'stages': [
                    {
                        'name': '基础阶段',
                        'duration_weeks': 12,
                        'skills': [
                            {'name': '移动开发基础', 'level': 1, 'priority': 'high'},
                            {'name': 'React Native/Flutter', 'level': 1, 'priority': 'high'},
                            {'name': '移动UI设计', 'level': 1, 'priority': 'medium'}
                        ]
                    },
                    {
                        'name': '进阶阶段',
                        'duration_weeks': 12,
                        'skills': [
                            {'name': '原生功能集成', 'level': 2, 'priority': 'high'},
                            {'name': '状态管理', 'level': 2, 'priority': 'medium'},
                            {'name': '数据持久化', 'level': 2, 'priority': 'high'}
                        ]
                    },
                    {
                        'name': '高级阶段',
                        'duration_weeks': 4,
                        'skills': [
                            {'name': '性能优化', 'level': 3, 'priority': 'medium'},
                            {'name': '应用发布', 'level': 3, 'priority': 'high'}
                        ]
                    }
                ]
            },
            'data_science': {
                'name': '数据科学',
                'description': '专注于数据分析、机器学习和AI应用',
                'duration_weeks': 30,
                'difficulty': 'advanced',
                'core_technologies': ['Python', 'SQL', 'Machine Learning', 'Statistics'],
                'stages': [
                    {
                        'name': '基础阶段',
                        'duration_weeks': 12,
                        'skills': [
                            {'name': 'Python数据处理', 'level': 1, 'priority': 'high'},
                            {'name': 'SQL数据库', 'level': 1, 'priority': 'high'},
                            {'name': '统计学基础', 'level': 1, 'priority': 'high'},
                            {'name': '数据可视化', 'level': 1, 'priority': 'medium'}
                        ]
                    },
                    {
                        'name': '进阶阶段',
                        'duration_weeks': 14,
                        'skills': [
                            {'name': '机器学习算法', 'level': 2, 'priority': 'high'},
                            {'name': '特征工程', 'level': 2, 'priority': 'high'},
                            {'name': '模型评估', 'level': 2, 'priority': 'high'},
                            {'name': '深度学习基础', 'level': 2, 'priority': 'medium'}
                        ]
                    },
                    {
                        'name': '高级阶段',
                        'duration_weeks': 4,
                        'skills': [
                            {'name': '深度学习应用', 'level': 3, 'priority': 'medium'},
                            {'name': '模型部署', 'level': 3, 'priority': 'high'},
                            {'name': 'MLOps', 'level': 3, 'priority': 'low'}
                        ]
                    }
                ]
            }
        }
    
    # 辅助方法
    def _process_learning_styles(self, styles: List[Dict]) -> Dict:
        """处理学习方式偏好"""
        preferences = {
            'hands_on': 0,
            'theoretical': 0,
            'video': 0,
            'reading': 0,
            'interactive': 0
        }
        
        for style in styles:
            if isinstance(style, dict):
                for key, value in style.items():
                    if key in preferences:
                        preferences[key] += value
        
        return preferences
    
    def _process_time_planning(self, plans: List[Dict]) -> Dict:
        """处理时间规划"""
        time_info = {
            'hours_per_week': 10,  # 默认值
            'preferred_schedule': 'flexible',
            'intensity': 'medium'
        }
        
        for plan in plans:
            if isinstance(plan, dict):
                if 'hours_per_week' in plan:
                    time_info['hours_per_week'] = plan['hours_per_week']
                if 'schedule' in plan:
                    time_info['preferred_schedule'] = plan['schedule']
                if 'intensity' in plan:
                    time_info['intensity'] = plan['intensity']
        
        return time_info
    
    def _determine_experience_level(self, skill_levels: Dict) -> str:
        """确定用户经验水平"""
        if not skill_levels:
            return 'beginner'
        
        avg_score = sum(s.get('combined_score', 0) for s in skill_levels.values()) / len(skill_levels)
        
        if avg_score < 0.3:
            return 'beginner'
        elif avg_score < 0.7:
            return 'intermediate'
        else:
            return 'advanced'
    
    def _calculate_goal_match(self, path: str, goals: List[Dict]) -> float:
        """计算目标匹配度"""
        if not goals:
            return 0.5  # 默认中等匹配
        
        # 这里可以根据具体的目标映射来计算
        # 暂时返回一个基础值
        return 0.6
    
    def _calculate_learning_match(self, path: str, preferences: Dict) -> float:
        """计算学习方式匹配度"""
        # 不同路径对学习方式的偏好
        path_preferences = {
            'frontend': {'hands_on': 0.8, 'interactive': 0.7, 'video': 0.6},
            'backend': {'theoretical': 0.6, 'hands_on': 0.8, 'reading': 0.7},
            'mobile': {'hands_on': 0.9, 'interactive': 0.6, 'video': 0.5},
            'data_science': {'theoretical': 0.8, 'reading': 0.7, 'hands_on': 0.6}
        }
        
        path_pref = path_preferences.get(path, {})
        if not path_pref or not preferences:
            return 0.5
        
        match_score = 0.0
        for style, weight in path_pref.items():
            user_pref = preferences.get(style, 0)
            match_score += user_pref * weight
        
        return min(1.0, match_score / len(path_pref))
    
    def _get_timeline_multiplier(self, time_availability: Dict) -> float:
        """根据时间可用性获取时间线倍数"""
        hours_per_week = time_availability.get('hours_per_week', 10)
        
        if hours_per_week >= 20:
            return 0.8  # 加速学习
        elif hours_per_week >= 15:
            return 1.0  # 标准速度
        elif hours_per_week >= 10:
            return 1.3  # 稍慢
        else:
            return 1.6  # 较慢
    
    def _recommend_supplementary_skills(self, primary_path: Dict, user_profile: Dict) -> List[Dict]:
        """推荐补充技能"""
        supplements = []
        
        # 根据主路径推荐相关技能
        path_name = primary_path['path_name']
        
        if path_name == 'frontend':
            supplements = [
                {'name': '基础设计知识', 'priority': 'medium', 'reason': '提升UI/UX能力'},
                {'name': '后端基础', 'priority': 'low', 'reason': '成为全栈开发者'}
            ]
        elif path_name == 'backend':
            supplements = [
                {'name': '前端基础', 'priority': 'medium', 'reason': '理解全栈开发'},
                {'name': 'DevOps基础', 'priority': 'medium', 'reason': '部署和运维能力'}
            ]
        elif path_name == 'mobile':
            supplements = [
                {'name': '后端API设计', 'priority': 'medium', 'reason': '更好的前后端协作'},
                {'name': 'UI/UX设计', 'priority': 'high', 'reason': '移动端用户体验'}
            ]
        elif path_name == 'data_science':
            supplements = [
                {'name': '云计算平台', 'priority': 'medium', 'reason': '大规模数据处理'},
                {'name': 'Web开发基础', 'priority': 'low', 'reason': '数据产品开发'}
            ]
        
        return supplements
    
    def _calculate_confidence_score(self, user_data: Dict, path_scores: Dict) -> float:
        """计算推荐置信度"""
        response_count = user_data.get('response_count', 0)
        max_score = max(path_scores.values()) if path_scores else 0
        
        # 基于回答完整度和最高分数计算置信度
        completeness_factor = min(1.0, response_count / 20)  # 假设20个问题为完整
        score_factor = max_score
        
        confidence = (completeness_factor * 0.6 + score_factor * 0.4)
        return round(confidence, 2)
    
    def _get_default_recommendation(self, user_id: str) -> Dict:
        """获取默认推荐（当推荐生成失败时）"""
        return {
            'user_id': user_id,
            'generated_at': datetime.utcnow().isoformat(),
            'primary_path': self.learning_paths['frontend'],
            'learning_plan': {},
            'confidence_score': 0.3,
            'is_default': True,
            'message': '推荐基于默认配置，建议完成更多问卷获得个性化推荐'
        }