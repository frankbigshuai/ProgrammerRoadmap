# test_user_model.py - 修复版本
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_user_model():
    """测试User模型的所有功能"""
    print("🚀 开始测试User模型...\n")
    
    try:
        # 初始化Flask应用和数据库
        from flask import Flask
        from config import DevelopmentConfig
        from app.utils.database import init_db
        from app.models.user import User
        
        app = Flask(__name__)
        app.config.from_object(DevelopmentConfig)
        
        with app.app_context():
            init_db(app)
            
            # 测试数据
            test_username = "testuser"
            test_email = "test@example.com"
            test_password = "password123"
            secret_key = app.config['SECRET_KEY']
            
            print("📝 测试1: 用户注册")
            # 创建用户
            user_id = User.create(test_username, test_email, test_password)
            if user_id:
                print(f"✅ 用户注册成功: {user_id}")
            else:
                print("❌ 用户注册失败")
                return False
            
            print("\n📝 测试2: 重复注册（应该失败）")
            # 测试重复注册
            duplicate_id = User.create(test_username, test_email, test_password)
            if not duplicate_id:
                print("✅ 重复注册被正确阻止")
            else:
                print("❌ 重复注册没有被阻止")
            
            print("\n📝 测试3: 用户名登录")
            # 测试用户名登录
            login_id = User.verify_login(test_username, test_password)
            if login_id == user_id:
                print(f"✅ 用户名登录成功: {login_id}")
            else:
                print("❌ 用户名登录失败")
            
            print("\n📝 测试4: 邮箱登录")
            # 测试邮箱登录
            email_login_id = User.verify_email_login(test_email, test_password)
            if email_login_id == user_id:
                print(f"✅ 邮箱登录成功: {email_login_id}")
            else:
                print("❌ 邮箱登录失败")
            
            print("\n📝 测试5: 错误密码登录（应该失败）")
            # 测试错误密码
            wrong_login = User.verify_login(test_username, "wrongpassword")
            if not wrong_login:
                print("✅ 错误密码被正确拒绝")
            else:
                print("❌ 错误密码没有被拒绝")
            
            print("\n📝 测试6: 获取用户资料")
            # 测试获取用户资料
            profile = User.get_profile(user_id)
            if profile and profile['username'] == test_username:
                print(f"✅ 获取用户资料成功: {profile['username']}")
            else:
                print("❌ 获取用户资料失败")
            
            print("\n📝 测试7: 问卷状态管理")
            # 测试问卷状态
            initial_status = User.has_completed_questionnaire(user_id)
            if not initial_status:
                print("✅ 初始问卷状态正确（未完成）")
            else:
                print("❌ 初始问卷状态错误")
            
            # 标记问卷完成
            mark_success = User.mark_questionnaire_completed(user_id)
            if mark_success:
                print("✅ 标记问卷完成成功")
                
                # 再次检查状态
                completed_status = User.has_completed_questionnaire(user_id)
                if completed_status:
                    print("✅ 问卷完成状态更新正确")
                else:
                    print("❌ 问卷完成状态更新失败")
            else:
                print("❌ 标记问卷完成失败")
            
            print("\n📝 测试8: JWT Token功能")
            # 测试JWT Token
            token = User.generate_token(user_id, secret_key)
            if token:
                print("✅ JWT Token生成成功")
                
                # 验证Token
                verified_user_id = User.verify_token(token, secret_key)
                if verified_user_id == user_id:
                    print("✅ JWT Token验证成功")
                else:
                    print("❌ JWT Token验证失败")
            else:
                print("❌ JWT Token生成失败")
            
            print("\n📝 测试9: 密码修改")
            # 测试密码修改
            new_password = "newpassword123"
            change_success = User.change_password(user_id, test_password, new_password)
            if change_success:
                print("✅ 密码修改成功")
                
                # 用新密码登录
                new_login = User.verify_login(test_username, new_password)
                if new_login == user_id:
                    print("✅ 新密码登录成功")
                else:
                    print("❌ 新密码登录失败")
            else:
                print("❌ 密码修改失败")
            
            print("\n📝 测试10: 清理测试数据")
            # 清理测试数据
            cleanup_success = User.deactivate(user_id)
            if cleanup_success:
                print("✅ 测试数据清理成功")
            else:
                print("❌ 测试数据清理失败")
            
            print("\n" + "="*50)
            print("🎉 User模型测试全部完成！")
            return True
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_user_model()
    if success:
        print("\n✅ 所有测试通过，User模型工作正常！")
        print("📋 下一步可以开始设计Question模型")
    else:
        print("\n❌ 有测试失败，请检查User模型实现")