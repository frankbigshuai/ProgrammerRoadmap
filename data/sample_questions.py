# data/sample_questions.py
"""示例问卷数据"""

SAMPLE_QUESTIONS = [
    {
        "question_id": "q1",
        "category": "experience",
        "question_text": "您的编程基础如何？",
        "type": "single_choice",
        "options": [
            {"value": "beginner", "text": "完全没有经验", "score": 1},
            {"value": "some_basic", "text": "学过一些基础语法", "score": 2},
            {"value": "can_code", "text": "能写简单程序", "score": 3},
            {"value": "experienced", "text": "有一定编程经验", "score": 4}
        ],
        "weight": 15,
        "order": 1
    },
    {
        "question_id": "q2",
        "category": "interest",
        "question_text": "您最感兴趣的开发方向是？",
        "type": "single_choice",
        "options": [
            {"value": "web", "text": "网站开发", "score": 1},
            {"value": "mobile", "text": "手机应用开发", "score": 1},
            {"value": "ai", "text": "人工智能/机器学习", "score": 1},
            {"value": "game", "text": "游戏开发", "score": 1}
        ],
        "weight": 20,
        "order": 2
    },
    {
        "question_id": "q3",
        "category": "goal",
        "question_text": "您的学习目标是什么？",
        "type": "single_choice",
        "options": [
            {"value": "job", "text": "找到编程相关工作", "score": 1},
            {"value": "skill", "text": "提升现有技能", "score": 1},
            {"value": "hobby", "text": "业余兴趣爱好", "score": 1},
            {"value": "startup", "text": "创业项目需要", "score": 1}
        ],
        "weight": 15,
        "order": 3
    }
]