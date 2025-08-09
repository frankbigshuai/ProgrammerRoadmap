# scripts/db_manager.py - 数据库管理工具
import sys
import os
import click
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app import create_app
    from app.utils.database import mongo, get_db_stats, cleanup_expired_data, backup_collection, health_check
    from app.models.question import Question
    from app.models.user import User
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在项目根目录下运行此脚本")
    sys.exit(1)

app = create_app()

@click.group()
def cli():
    """数据库管理工具"""
    pass

@cli.command()
def status():
    """检查数据库状态"""
    with app.app_context():
        health = health_check()
        click.echo(f"数据库状态: {health['status']}")
        
        if health['status'] == 'healthy':
            click.echo(f"数据库名称: {health['database']}")
            click.echo(f"集合数量: {health['collections_count']}")
            click.echo(f"总大小: {health['total_size_bytes']} bytes")
            click.echo(f"响应时间: {health['connection']['response_time_ms']:.2f}ms")
        else:
            click.echo(f"错误信息: {health['message']}")

@cli.command()
def stats():
    """显示详细统计信息"""
    with app.app_context():
        stats = get_db_stats()
        if stats:
            click.echo(f"\n📊 数据库统计信息:")
            click.echo(f"数据库: {stats['database']}")
            click.echo(f"总大小: {stats['total_size']} bytes\n")
            
            for collection, info in stats['collections'].items():
                click.echo(f"📁 {collection}:")
                click.echo(f"  文档数量: {info['count']}")
                click.echo(f"  存储大小: {info['size']} bytes")
                click.echo(f"  平均文档大小: {info['avgObjSize']} bytes\n")

@cli.command()
def cleanup():
    """清理过期数据"""
    with app.app_context():
        click.echo("🧹 开始清理过期数据...")
        result = cleanup_expired_data()
        
        if result:
            click.echo(f"✅ 清理完成:")
            click.echo(f"  过期推荐: {result['recommendations_cleaned']} 条")
            click.echo(f"  过期反馈: {result['feedback_cleaned']} 条")
        else:
            click.echo("❌ 清理失败")

@cli.command()
@click.argument('collection_name')
@click.option('--path', default=None, help='备份文件路径')
def backup(collection_name, path):
    """备份指定集合"""
    with app.app_context():
        click.echo(f"💾 备份集合: {collection_name}")
        backup_path = backup_collection(collection_name, path)
        
        if backup_path:
            click.echo(f"✅ 备份完成: {backup_path}")
        else:
            click.echo("❌ 备份失败")

@cli.command()
def init_questions():
    """初始化示例问题数据"""
    with app.app_context():
        click.echo("📝 初始化示例问题...")
        
        # 示例问题数据
        sample_questions = [
            {
                "question_id": "skill_001",
                "category": "skill_assessment",
                "question_text": "你的编程经验水平如何？",
                "question_type": "single_choice",  # 修改参数名
                "order": 1,
                "weight": 2,
                "options": [
                    {
                        "value": "beginner",
                        "text": "初学者（0-1年）",
                        "skill_mapping": {
                            "all_paths": {"level": 0.1, "foundation": 0.2}
                        }
                    },
                    {
                        "value": "intermediate",
                        "text": "中级（1-3年）",
                        "skill_mapping": {
                            "all_paths": {"level": 0.5, "foundation": 0.6}
                        }
                    },
                    {
                        "value": "advanced",
                        "text": "高级（3年以上）",
                        "skill_mapping": {
                            "all_paths": {"level": 0.8, "foundation": 0.9}
                        }
                    }
                ]
            },
            {
                "question_id": "interest_001",
                "category": "interest_preference",
                "question_text": "你对哪个技术方向最感兴趣？",
                "question_type": "single_choice",  # 修改参数名
                "order": 1,
                "weight": 3,
                "options": [
                    {
                        "value": "web_frontend",
                        "text": "前端开发",
                        "path_weights": {
                            "frontend": 0.9,
                            "backend": 0.2,
                            "mobile": 0.3,
                            "data_science": 0.1
                        }
                    },
                    {
                        "value": "web_backend",
                        "text": "后端开发",
                        "path_weights": {
                            "frontend": 0.2,
                            "backend": 0.9,
                            "mobile": 0.2,
                            "data_science": 0.3
                        }
                    },
                    {
                        "value": "mobile_dev",
                        "text": "移动开发",
                        "path_weights": {
                            "frontend": 0.4,
                            "backend": 0.3,
                            "mobile": 0.9,
                            "data_science": 0.1
                        }
                    },
                    {
                        "value": "data_ai",
                        "text": "数据科学/AI",
                        "path_weights": {
                            "frontend": 0.1,
                            "backend": 0.4,
                            "mobile": 0.1,
                            "data_science": 0.9
                        }
                    }
                ]
            }
        ]
        
        created_count = 0
        skipped_count = 0
        
        for question_data in sample_questions:
            try:
                result = Question.create(**question_data)
                if result:
                    created_count += 1
                    click.echo(f"✅ 创建问题: {question_data['question_id']}")
                else:
                    skipped_count += 1
                    click.echo(f"⚠️ 问题已存在: {question_data['question_id']}")
            except Exception as e:
                skipped_count += 1
                click.echo(f"❌ 创建问题失败 {question_data['question_id']}: {e}")
        
        click.echo(f"\n📝 初始化完成:")
        click.echo(f"  新创建: {created_count} 个问题")
        click.echo(f"  跳过: {skipped_count} 个问题")

@cli.command()
def create_admin():
    """创建管理员用户"""
    with app.app_context():
        username = click.prompt("管理员用户名")
        email = click.prompt("管理员邮箱")
        password = click.prompt("密码", hide_input=True, confirmation_prompt=True)
        
        user_id = User.create(username, email, password)
        if user_id:
            click.echo(f"✅ 管理员用户创建成功: {user_id}")
        else:
            click.echo("❌ 用户创建失败，可能用户名或邮箱已存在")

@cli.command()
@click.option('--drop', is_flag=True, help='删除所有数据')
def reset(drop):
    """重置数据库"""
    if drop:
        confirm = click.confirm("⚠️ 这将删除所有数据，确定要继续吗？")
        if confirm:
            with app.app_context():
                db = mongo.db
                for collection in db.list_collection_names():
                    db[collection].drop()
                    click.echo(f"🗑️ 删除集合: {collection}")
                
                # 重新创建索引
                from app.utils.database import _create_indexes, _ensure_collections
                _ensure_collections()
                _create_indexes()
                
                click.echo("✅ 数据库重置完成")

if __name__ == '__main__':
    cli()