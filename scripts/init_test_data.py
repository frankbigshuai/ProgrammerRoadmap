# scripts/init_complete_questions.py - 完整问题数据初始化
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.question import Question

app = create_app()

def init_complete_questions():
    """初始化完整的问卷数据"""
    
    questions_data = [
        # === 技能评估类 ===
        {
            "question_id": "skill_001",
            "category": "skill_assessment",
            "question_text": "你的编程经验水平如何？",
            "question_type": "single_choice",
            "order": 1,
            "weight": 3,
            "options": [
                {
                    "value": "beginner",
                    "text": "初学者（0-1年编程经验）",
                    "skill_mapping": {
                        "all_paths": {"level": 0.1, "foundation": 0.2}
                    }
                },
                {
                    "value": "intermediate",
                    "text": "中级开发者（1-3年经验）",
                    "skill_mapping": {
                        "all_paths": {"level": 0.5, "foundation": 0.6}
                    }
                },
                {
                    "value": "advanced",
                    "text": "高级开发者（3年以上）",
                    "skill_mapping": {
                        "all_paths": {"level": 0.8, "foundation": 0.9}
                    }
                }
            ]
        },
        {
            "question_id": "skill_002",
            "category": "skill_assessment",
            "question_text": "你对前端技术的了解程度？",
            "question_type": "single_choice",
            "order": 2,
            "weight": 2,
            "options": [
                {
                    "value": "none",
                    "text": "完全不了解",
                    "skill_mapping": {
                        "frontend": {"level": 0.0, "foundation": 0.0}
                    }
                },
                {
                    "value": "basic",
                    "text": "了解HTML/CSS基础",
                    "skill_mapping": {
                        "frontend": {"level": 0.3, "foundation": 0.4}
                    }
                },
                {
                    "value": "intermediate",
                    "text": "会使用JavaScript和框架",
                    "skill_mapping": {
                        "frontend": {"level": 0.6, "foundation": 0.7}
                    }
                },
                {
                    "value": "advanced",
                    "text": "精通现代前端开发",
                    "skill_mapping": {
                        "frontend": {"level": 0.9, "foundation": 0.9}
                    }
                }
            ]
        },
        {
            "question_id": "skill_003",
            "category": "skill_assessment",
            "question_text": "你对后端开发的了解程度？",
            "question_type": "single_choice",
            "order": 3,
            "weight": 2,
            "options": [
                {
                    "value": "none",
                    "text": "完全不了解",
                    "skill_mapping": {
                        "backend": {"level": 0.0, "foundation": 0.0}
                    }
                },
                {
                    "value": "basic",
                    "text": "了解API和数据库概念",
                    "skill_mapping": {
                        "backend": {"level": 0.3, "foundation": 0.4}
                    }
                },
                {
                    "value": "intermediate",
                    "text": "会使用后端框架开发",
                    "skill_mapping": {
                        "backend": {"level": 0.6, "foundation": 0.7}
                    }
                },
                {
                    "value": "advanced",
                    "text": "精通服务端架构设计",
                    "skill_mapping": {
                        "backend": {"level": 0.9, "foundation": 0.9}
                    }
                }
            ]
        },
        
        # === 兴趣偏好类 ===
        {
            "question_id": "interest_001",
            "category": "interest_preference",
            "question_text": "你对哪个技术方向最感兴趣？",
            "question_type": "single_choice",
            "order": 1,
            "weight": 3,
            "options": [
                {
                    "value": "web_frontend",
                    "text": "前端开发 - 创建用户界面和交互",
                    "path_weights": {
                        "frontend": 0.9,
                        "backend": 0.2,
                        "mobile": 0.3,
                        "data_science": 0.1
                    }
                },
                {
                    "value": "web_backend",
                    "text": "后端开发 - 服务器逻辑和数据处理",
                    "path_weights": {
                        "frontend": 0.2,
                        "backend": 0.9,
                        "mobile": 0.2,
                        "data_science": 0.3
                    }
                },
                {
                    "value": "mobile_dev",
                    "text": "移动开发 - iOS/Android应用",
                    "path_weights": {
                        "frontend": 0.4,
                        "backend": 0.3,
                        "mobile": 0.9,
                        "data_science": 0.1
                    }
                },
                {
                    "value": "data_ai",
                    "text": "数据科学/AI - 数据分析和机器学习",
                    "path_weights": {
                        "frontend": 0.1,
                        "backend": 0.4,
                        "mobile": 0.1,
                        "data_science": 0.9
                    }
                }
            ]
        },
        {
            "question_id": "interest_002",
            "category": "interest_preference",
            "question_text": "你更喜欢哪种工作类型？",
            "question_type": "single_choice",
            "order": 2,
            "weight": 2,
            "options": [
                {
                    "value": "visual_creative",
                    "text": "视觉创意 - 设计和用户体验",
                    "path_weights": {
                        "frontend": 0.8,
                        "backend": 0.1,
                        "mobile": 0.6,
                        "data_science": 0.2
                    }
                },
                {
                    "value": "logic_systems",
                    "text": "逻辑系统 - 架构和算法",
                    "path_weights": {
                        "frontend": 0.2,
                        "backend": 0.8,
                        "mobile": 0.3,
                        "data_science": 0.7
                    }
                },
                {
                    "value": "user_interaction",
                    "text": "用户交互 - 产品和功能设计",
                    "path_weights": {
                        "frontend": 0.7,
                        "backend": 0.3,
                        "mobile": 0.8,
                        "data_science": 0.2
                    }
                },
                {
                    "value": "data_analysis",
                    "text": "数据洞察 - 分析和预测",
                    "path_weights": {
                        "frontend": 0.2,
                        "backend": 0.5,
                        "mobile": 0.2,
                        "data_science": 0.9
                    }
                }
            ]
        },
        
        # === 职业目标类 ===
        {
            "question_id": "goal_001",
            "category": "career_goal",
            "question_text": "你的短期职业目标是什么？（1-2年内）",
            "question_type": "single_choice",
            "order": 1,
            "weight": 3,
            "options": [
                {
                    "value": "get_first_job",
                    "text": "获得第一份程序员工作",
                    "goal_mapping": {
                        "timeline": "short",
                        "focus": "employment",
                        "priority": "practical_skills"
                    }
                },
                {
                    "value": "switch_career",
                    "text": "转行进入技术领域",
                    "goal_mapping": {
                        "timeline": "short",
                        "focus": "transition",
                        "priority": "foundational_knowledge"
                    }
                },
                {
                    "value": "skill_upgrade",
                    "text": "提升现有技术技能",
                    "goal_mapping": {
                        "timeline": "short",
                        "focus": "advancement",
                        "priority": "specialized_skills"
                    }
                },
                {
                    "value": "startup_project",
                    "text": "开发自己的项目/产品",
                    "goal_mapping": {
                        "timeline": "short",
                        "focus": "entrepreneurship",
                        "priority": "full_stack_skills"
                    }
                }
            ]
        },
        
        # === 学习方式类 ===
        {
            "question_id": "style_001",
            "category": "learning_style",
            "question_text": "你偏好哪种学习方式？",
            "question_type": "single_choice",
            "order": 1,
            "weight": 2,
            "options": [
                {
                    "value": "hands_on",
                    "text": "动手实践 - 通过项目学习",
                    "style_mapping": {
                        "hands_on": 0.9,
                        "theoretical": 0.2,
                        "video": 0.6,
                        "reading": 0.4,
                        "interactive": 0.7
                    }
                },
                {
                    "value": "structured",
                    "text": "系统学习 - 按课程体系",
                    "style_mapping": {
                        "hands_on": 0.4,
                        "theoretical": 0.8,
                        "video": 0.7,
                        "reading": 0.8,
                        "interactive": 0.5
                    }
                },
                {
                    "value": "visual",
                    "text": "视觉学习 - 图表和视频",
                    "style_mapping": {
                        "hands_on": 0.5,
                        "theoretical": 0.3,
                        "video": 0.9,
                        "reading": 0.2,
                        "interactive": 0.8
                    }
                },
                {
                    "value": "social",
                    "text": "协作学习 - 讨论和交流",
                    "style_mapping": {
                        "hands_on": 0.6,
                        "theoretical": 0.4,
                        "video": 0.3,
                        "reading": 0.5,
                        "interactive": 0.9
                    }
                }
            ]
        },
        
        # === 时间规划类 ===
        {
            "question_id": "time_001",
            "category": "time_planning",
            "question_text": "你每周能投入多少时间学习编程？",
            "question_type": "single_choice",
            "order": 1,
            "weight": 2,
            "options": [
                {
                    "value": "part_time",
                    "text": "5-10小时（业余时间）",
                    "time_mapping": {
                        "hours_per_week": 7.5,
                        "intensity": "low",
                        "schedule": "flexible"
                    }
                },
                {
                    "value": "committed",
                    "text": "10-20小时（比较投入）",
                    "time_mapping": {
                        "hours_per_week": 15,
                        "intensity": "medium",
                        "schedule": "regular"
                    }
                },
                {
                    "value": "intensive",
                    "text": "20-40小时（高强度学习）",
                    "time_mapping": {
                        "hours_per_week": 30,
                        "intensity": "high",
                        "schedule": "structured"
                    }
                },
                {
                    "value": "full_time",
                    "text": "40+小时（全职学习）",
                    "time_mapping": {
                        "hours_per_week": 50,
                        "intensity": "very_high",
                        "schedule": "full_time"
                    }
                }
            ]
        },
        {
            "question_id": "time_002", 
            "category": "time_planning",
            "question_text": "你希望多长时间内看到明显进步？",
            "question_type": "single_choice",
            "order": 2,
            "weight": 2,
            "options": [
                {
                    "value": "quick_wins",
                    "text": "1-3个月（快速上手）",
                    "time_mapping": {
                        "timeline_expectation": "short",
                        "pace": "fast",
                        "milestone_frequency": "weekly"
                    }
                },
                {
                    "value": "steady_progress",
                    "text": "3-6个月（稳步提升）",
                    "time_mapping": {
                        "timeline_expectation": "medium",
                        "pace": "steady",
                        "milestone_frequency": "monthly"
                    }
                },
                {
                    "value": "thorough_mastery",
                    "text": "6-12个月（深入掌握）",
                    "time_mapping": {
                        "timeline_expectation": "long",
                        "pace": "thorough",
                        "milestone_frequency": "quarterly"
                    }
                }
            ]
        }
    ]
    
    return questions_data

def main():
    """主函数"""
    with app.app_context():
        print("📝 开始初始化完整问卷数据...")
        
        questions_data = init_complete_questions()
        
        created_count = 0
        updated_count = 0
        error_count = 0
        
        for question_data in questions_data:
            try:
                # 检查问题是否已存在
                existing = Question.get_by_id(question_data['question_id'])
                
                if existing:
                    print(f"⚠️ 问题已存在，跳过: {question_data['question_id']}")
                    updated_count += 1
                else:
                    result = Question.create(**question_data)
                    if result:
                        created_count += 1
                        print(f"✅ 创建问题: {question_data['question_id']} - {question_data['question_text'][:30]}...")
                    else:
                        error_count += 1
                        print(f"❌ 创建失败: {question_data['question_id']}")
                        
            except Exception as e:
                error_count += 1
                print(f"❌ 处理问题失败 {question_data['question_id']}: {e}")
        
        print(f"\n📊 初始化完成:")
        print(f"  ✅ 新创建: {created_count} 个问题")
        print(f"  ⚠️ 已存在: {updated_count} 个问题") 
        print(f"  ❌ 创建失败: {error_count} 个问题")
        print(f"  📝 总计: {len(questions_data)} 个问题")
        
        # 显示各分类统计
        print(f"\n📋 分类统计:")
        categories = {}
        for q in questions_data:
            cat = q['category']
            categories[cat] = categories.get(cat, 0) + 1
            
        for category, count in categories.items():
            print(f"  {category}: {count} 个问题")

if __name__ == '__main__':
    main()