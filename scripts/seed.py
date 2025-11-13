"""初始化样例数据"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal
from app.db import SessionLocal, init_db
from app.models.user import User
from app.models.dish import Category, Dish, OptionGroup, OptionItem
from app.models.enums import DishStatus, OptionType


def seed_data():
    """插入样例数据"""
    # 初始化数据库
    init_db()
    
    db = SessionLocal()
    try:
        # 检查是否已有数据
        if db.query(User).count() > 0:
            print("⚠️  数据库已有数据，跳过初始化")
            return
        
        print("🌱 开始初始化样例数据...")
        
        # 1. 创建管理员用户
        admin = User(username="admin", is_admin=True)
        db.add(admin)
        print("✅ 创建管理员用户: admin")
        
        # 2. 创建分类
        categories = [
            Category(name="特色菜", sort_order=1),
            Category(name="肉类", sort_order=2),
            Category(name="素菜", sort_order=3),
            Category(name="酒水", sort_order=4),
            Category(name="主食", sort_order=5),
        ]
        db.add_all(categories)
        db.flush()  # 获取 category_id
        print("✅ 创建5个分类")
        
        # 3. 创建菜品
        dishes_data = [
            # 特色菜
            {"cat": 0, "name": "宫保鸡丁", "price": 38, "stock": 20},
            {"cat": 0, "name": "麻婆豆腐", "price": 28, "stock": 30},
            {"cat": 0, "name": "水煮鱼", "price": 68, "stock": 15},
            {"cat": 0, "name": "鱼香肉丝", "price": 32, "stock": 25},
            
            # 肉类
            {"cat": 1, "name": "红烧肉", "price": 48, "stock": 18},
            {"cat": 1, "name": "糖醋排骨", "price": 42, "stock": 22},
            {"cat": 1, "name": "清蒸鲈鱼", "price": 58, "stock": 10},
            {"cat": 1, "name": "口水鸡", "price": 36, "stock": 20},
            
            # 素菜
            {"cat": 2, "name": "清炒时蔬", "price": 18, "stock": 50},
            {"cat": 2, "name": "干煸豆角", "price": 22, "stock": 35},
            {"cat": 2, "name": "蒜蓉西兰花", "price": 20, "stock": 40},
            {"cat": 2, "name": "凉拌黄瓜", "price": 12, "stock": 60},
            
            # 酒水
            {"cat": 3, "name": "可口可乐", "price": 6, "stock": 100},
            {"cat": 3, "name": "鲜榨橙汁", "price": 15, "stock": 30},
            {"cat": 3, "name": "冰镇酸梅汤", "price": 10, "stock": 50},
            {"cat": 3, "name": "青岛啤酒", "price": 12, "stock": 80},
            
            # 主食
            {"cat": 4, "name": "米饭", "price": 3, "stock": 200},
            {"cat": 4, "name": "炒饭", "price": 15, "stock": 50},
            {"cat": 4, "name": "刀削面", "price": 18, "stock": 40},
            {"cat": 4, "name": "馒头", "price": 2, "stock": 100},
        ]
        
        dishes = []
        for data in dishes_data:
            dish = Dish(
                category_id=categories[data["cat"]].category_id,
                name=data["name"],
                price=Decimal(str(data["price"])),
                image_url="",
                stock=data["stock"],
                status=DishStatus.ON_SHELF
            )
            dishes.append(dish)
        
        db.add_all(dishes)
        db.flush()
        print(f"✅ 创建{len(dishes)}道菜品")
        
        # 4. 为部分菜品添加口味选项
        # 宫保鸡丁 - 辣度（单选）
        spicy_group = OptionGroup(
            dish_id=dishes[0].dish_id,
            name="辣度",
            type=OptionType.SINGLE,
            required=True,
            max_select=1
        )
        db.add(spicy_group)
        db.flush()
        
        spicy_options = [
            OptionItem(group_id=spicy_group.group_id, name="微辣", price_delta=Decimal("0")),
            OptionItem(group_id=spicy_group.group_id, name="中辣", price_delta=Decimal("0")),
            OptionItem(group_id=spicy_group.group_id, name="特辣", price_delta=Decimal("2")),
        ]
        db.add_all(spicy_options)
        
        # 水煮鱼 - 分量（单选）
        portion_group = OptionGroup(
            dish_id=dishes[2].dish_id,
            name="分量",
            type=OptionType.SINGLE,
            required=False,
            max_select=1
        )
        db.add(portion_group)
        db.flush()
        
        portion_options = [
            OptionItem(group_id=portion_group.group_id, name="小份", price_delta=Decimal("-10")),
            OptionItem(group_id=portion_group.group_id, name="标准", price_delta=Decimal("0")),
            OptionItem(group_id=portion_group.group_id, name="大份", price_delta=Decimal("15")),
        ]
        db.add_all(portion_options)
        
        # 鲜榨橙汁 - 加料（多选）
        addon_group = OptionGroup(
            dish_id=dishes[13].dish_id,
            name="加料",
            type=OptionType.MULTIPLE,
            required=False,
            max_select=3
        )
        db.add(addon_group)
        db.flush()
        
        addon_options = [
            OptionItem(group_id=addon_group.group_id, name="加冰", price_delta=Decimal("0")),
            OptionItem(group_id=addon_group.group_id, name="少糖", price_delta=Decimal("0")),
            OptionItem(group_id=addon_group.group_id, name="加柠檬", price_delta=Decimal("2")),
        ]
        db.add_all(addon_options)
        
        print("✅ 创建口味选项")
        
        # 提交事务
        db.commit()
        print("\n🎉 样例数据初始化完成！")
        print("\n📊 数据统计:")
        print(f"  - 用户: 1 (admin)")
        print(f"  - 分类: 5")
        print(f"  - 菜品: {len(dishes)}")
        print(f"  - 口味选项组: 3")
        print(f"  - 口味选项: 9")
        print("\n💡 管理员账号: admin")
        print("💡 前台访问: http://localhost:8000/")
        print("💡 后台管理: http://localhost:8000/admin")
        print("💡 API文档: http://localhost:8000/docs")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 初始化失败: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()

