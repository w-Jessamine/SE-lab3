"""菜品与分类服务"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.dish import Category, Dish
from app.schemas.dish import CategoryResponse, DishResponse


class MenuService:
    """菜品浏览服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_categories(self) -> List[CategoryResponse]:
        """
        获取所有分类
        契约：按 sort_order 升序返回
        """
        categories = self.db.query(Category).order_by(Category.sort_order).all()
        return [CategoryResponse.model_validate(cat) for cat in categories]
    
    def get_dishes_by_category(
        self,
        category_id: Optional[int] = None,
        page: int = 1,
        size: int = 20
    ) -> List[DishResponse]:
        """
        分页查询菜品
        参数：
          - category_id: 可选，筛选分类
          - page: 页码（从1开始）
          - size: 每页数量
        契约：返回菜品列表
        """
        query = self.db.query(Dish)
        
        # 按分类筛选
        if category_id is not None:
            query = query.filter(Dish.category_id == category_id)
        
        # 分页
        offset = (page - 1) * size
        dishes = query.offset(offset).limit(size).all()
        
        return [DishResponse.model_validate(dish) for dish in dishes]
    
    def get_dish_detail(self, dish_id: int) -> Optional[Dish]:
        """
        获取菜品详情（含口味配置）
        契约：若不存在返回 None
        """
        return self.db.query(Dish).filter(Dish.dish_id == dish_id).first()
    
    def create_dish(self, category_id: int, name: str, price: float, 
                   image_url: str, stock: int, status: str) -> Dish:
        """创建菜品（管理员）"""
        from app.models.enums import DishStatus
        dish = Dish(
            category_id=category_id,
            name=name,
            price=price,
            image_url=image_url,
            stock=stock,
            status=DishStatus(status)
        )
        self.db.add(dish)
        self.db.commit()
        self.db.refresh(dish)
        return dish
    
    def update_dish_status(self, dish_id: int, status: str) -> Dish:
        """上下架菜品"""
        from app.models.enums import DishStatus
        dish = self.get_dish_detail(dish_id)
        if not dish:
            raise ValueError(f"菜品不存在：dish_id={dish_id}")
        
        dish.status = DishStatus(status)
        self.db.commit()
        self.db.refresh(dish)
        return dish

