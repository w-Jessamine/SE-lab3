# 📁 项目结构

```
lab3/
├── README.md                    # 项目说明文档
├── QUICKSTART.md                # 快速启动指南
├── GIT_REMOTE_SETUP.md          # Git 远程仓库托管指南
├── PROJECT_STRUCTURE.md         # 本文件：项目结构说明
│
├── requirements.txt             # Python 依赖列表
├── .gitignore                   # Git 忽略文件
│
├── UML/                         # UML 设计图
│   ├── 类图.puml / 类图.png
│   ├── 序列图.puml / 序列图.png
│   ├── 用例图.puml / 用例图.png
│   └── 组件图.puml / 组件图.png
│
├── app/                         # 应用主目录
│   ├── __init__.py
│   ├── main.py                  # FastAPI 入口（路由挂载、启动配置）
│   ├── config.py                # 配置管理（数据库连接等）
│   ├── db.py                    # SQLAlchemy 会话管理
│   │
│   ├── models/                  # 数据模型层（SQLAlchemy ORM）
│   │   ├── __init__.py
│   │   ├── enums.py             # 枚举类型（DishStatus, OrderStatus, OptionType）
│   │   ├── user.py              # 用户模型（User）
│   │   ├── dish.py              # 菜品模型（Category, Dish, OptionGroup, OptionItem）
│   │   └── order.py             # 订单模型（Order, OrderItem, order_item_options 中间表）
│   │
│   ├── schemas/                 # 数据传输对象（Pydantic DTO）
│   │   ├── __init__.py
│   │   ├── user.py              # UserLogin, UserResponse
│   │   ├── dish.py              # CategoryResponse, DishResponse, DishCreate
│   │   ├── option.py            # OptionGroupResponse, OptionItemResponse
│   │   └── order.py             # OrderCreate, OrderItemCreate, OrderResponse
│   │
│   ├── services/                # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── menu_service.py      # 菜品浏览、分类查询
│   │   ├── inventory_service.py # 库存查询、扣减、调整
│   │   └── order_service.py     # 订单创建、状态变更（核心事务逻辑）
│   │
│   ├── api/                     # 路由层（控制器）
│   │   ├── __init__.py
│   │   ├── auth.py              # POST /api/login（假登录）
│   │   ├── menu.py              # GET /api/categories, /dishes, /stock
│   │   ├── order.py             # POST /api/orders, GET /orders/{id}, POST /orders/{id}/cancel
│   │   └── admin.py             # 后台管理接口（菜品、库存、订单）
│   │
│   └── pages/                   # Jinja2 模板（HTML）
│       ├── index.html           # 前台主页（菜品浏览、购物车）
│       ├── checkout.html        # 下单确认页
│       └── admin.html           # 后台管理页（库存、订单）
│
├── tests/                       # 测试用例
│   ├── __init__.py
│   ├── conftest.py              # pytest 配置与 fixtures
│   ├── test_inventory.py        # 库存服务测试（10 个用例）
│   ├── test_order.py            # 订单业务测试（6 个用例）
│   └── test_concurrency.py      # 并发测试（防超卖）
│
└── scripts/                     # 工具脚本
    ├── seed.py                  # 数据初始化（创建表、插入样例数据）
    ├── check_style.sh           # 代码风格检查（Black + Ruff + Pylint）
    └── count_lines.sh           # 代码行数统计
```

---

## 📊 代码统计（实际）

### 按模块统计

| 模块 | 文件数 | 行数 | 功能 |
|------|--------|------|------|
| **models** | 4 | ~220 | 数据模型定义（User, Dish, Order 等） |
| **schemas** | 4 | ~150 | Pydantic DTO（请求/响应模型） |
| **services** | 3 | ~380 | 业务逻辑（菜品、库存、订单服务） |
| **api** | 4 | ~240 | 路由层（控制器） |
| **config/db** | 2 | ~60 | 配置与数据库管理 |
| **main** | 1 | ~50 | FastAPI 入口 |
| **tests** | 3 | ~350 | 测试用例 |
| **scripts** | 1 | ~100 | 数据初始化脚本 |
| **总计** | 22 | **~1185** | Python 代码（不含模板） |

### 模板文件

| 文件 | 行数 | 说明 |
|------|------|------|
| `index.html` | ~250 | 前台主页（响应式设计） |
| `checkout.html` | ~150 | 下单确认页 |
| `admin.html` | ~220 | 后台管理页 |
| **总计** | **~620** | HTML + CSS + JavaScript |

---

## 🎯 核心文件说明

### 1. 入口与配置

- **`app/main.py`**: FastAPI 应用入口，挂载所有路由，配置 Jinja2 模板
- **`app/config.py`**: 配置管理（数据库URL、环境变量）
- **`app/db.py`**: SQLAlchemy 引擎、会话工厂、`get_db()` 依赖注入

### 2. 数据模型层（models/）

- **`enums.py`**: 定义 `DishStatus`, `OrderStatus`, `OptionType` 枚举
- **`user.py`**: `User` 模型（username, is_admin）
- **`dish.py`**: `Category`, `Dish`, `OptionGroup`, `OptionItem` 模型
- **`order.py`**: `Order`, `OrderItem` 模型，`order_item_options` 中间表

**关键方法：**
- `Dish.is_available()`: 判断菜品是否可下单（`status==OnShelf AND stock > 0`）
- `Dish.update_stock(delta)`: 调整库存（可正可负）
- `OrderItem.subtotal()`: 计算订单项小计（含口味加价）
- `Order.total_price()`: 计算订单总价

### 3. 业务逻辑层（services/）

#### `menu_service.py` - 菜品服务

- `get_all_categories()`: 获取所有分类
- `get_dishes_by_category()`: 分页查询菜品
- `get_dish_detail()`: 查询菜品详情（含口味选项）
- `create_dish()`, `update_dish_status()`: 管理员功能

#### `inventory_service.py` - 库存服务

- `check_stock()`: 检查库存是否充足
- `deduct_stock()`: 扣减库存（事务内调用）
- `adjust_stock()`: 管理员手动调整库存
- `get_stock()`: 查询实时库存

#### `order_service.py` - 订单服务（核心）

- **`create_order()`**: 创建订单（事务保证一致性）
  - 开启事务
  - 对涉及的 `Dish` 行加锁（`with_for_update()`）
  - 校验菜品状态与库存
  - 计算总价（含口味加价）
  - 扣减库存
  - 插入订单、订单项、选项关联
  - 提交事务（失败则回滚）

- `cancel_order()`, `complete_order()`: 状态变更
- `get_order_by_id()`, `list_orders()`: 查询订单

### 4. 路由层（api/）

- **`auth.py`**: 假登录接口（不存在则创建用户）
- **`menu.py`**: 菜品浏览接口（分类、菜品列表、库存查询）
- **`order.py`**: 订单接口（创建、查询、取消）
- **`admin.py`**: 后台管理接口（菜品管理、库存调整、订单管理）

### 5. 前端模板（pages/）

#### `index.html` - 主页

- 响应式菜品卡片网格布局
- 分类切换（全部/特色/肉类/素菜/酒水/主食）
- 实时显示库存状态（充足/库存少/已售罄）
- 购物车数量统计，悬浮购物车按钮
- 使用 localStorage 持久化用户和购物车

#### `checkout.html` - 下单页

- 显示购物车明细（菜品、单价、数量、小计）
- 备注输入框
- 订单总价实时计算
- 提交后调用 `POST /api/orders` 创建订单

#### `admin.html` - 后台管理页

- Tab 切换（库存管理、订单管理）
- 库存管理：调整库存、上下架菜品
- 订单管理：订单列表、状态筛选、完成订单

---

## 🔄 数据流

### 用户下单流程

```
用户 → index.html → 浏览菜品 → 添加到购物车（localStorage）
                  ↓
          checkout.html → 确认订单 → POST /api/orders
                                         ↓
                                   OrderService.create_order()
                                         ↓
                      ┌──────────────────┴──────────────────┐
                      ↓                                     ↓
            InventoryService.deduct_stock()    插入 Order + OrderItem
                      ↓                                     ↓
            UPDATE dishes SET stock=stock-qty    INSERT INTO orders
                      ↓                                     ↓
                   事务提交（成功）/ 回滚（失败）
                                         ↓
                            返回 OrderResponse
```

### 后台库存调整流程

```
管理员 → admin.html → 输入 dish_id + delta → POST /api/admin/inventory/adjust
                                                        ↓
                                          InventoryService.adjust_stock()
                                                        ↓
                                          Dish.update_stock(delta)
                                                        ↓
                                          db.commit() → 更新成功
```

---

## 🧪 测试覆盖

### `test_inventory.py` - 库存测试（10 个用例）

1. ✅ 库存充足时返回 True
2. ✅ 库存不足时返回 False
3. ✅ 下架菜品返回 False
4. ✅ 扣减库存成功
5. ✅ 扣减库存失败（库存不足）
6. ✅ 增加库存
7. ✅ 减少库存
8. ✅ 减少库存失败（会导致负数）
9. ✅ 查询库存

### `test_order.py` - 订单测试（6 个用例）

1. ✅ 正常下单成功（验证总价与库存扣减）
2. ✅ 库存不足时抛出 ValueError
3. ✅ 菜品下架时抛出 ValueError
4. ✅ 取消订单状态变更
5. ✅ 完成订单状态变更
6. ✅ 带口味选项的订单（验证加价计算）

### `test_concurrency.py` - 并发测试（2 个用例）

1. ✅ 防止超卖（两用户同时下单有限库存，一成功一失败）
2. ✅ 顺序下单对比（验证基本逻辑）

---

## 🏗️ 架构特点

### 1. 三层架构

- **路由层（api/）**: 参数校验、HTTP 响应
- **服务层（services/）**: 业务逻辑、事务管理
- **数据层（models/）**: ORM 模型、数据访问

### 2. 依赖注入

使用 FastAPI 的 `Depends(get_db)` 实现数据库会话注入

### 3. 事务管理

- 订单创建在单个事务内完成（库存扣减 + 订单写入）
- 使用 `with_for_update()` 行锁防止并发超卖
- 失败自动回滚

### 4. 响应式前端

- 使用原生 HTML + CSS + JavaScript
- 渐变色背景、卡片式布局
- 媒体查询适配移动端

---

## 📦 数据库表结构

| 表名 | 字段 | 说明 |
|------|------|------|
| `users` | user_id, username, is_admin | 用户表 |
| `categories` | category_id, name, sort_order | 分类表 |
| `dishes` | dish_id, category_id, name, price, image_url, stock, status | 菜品表 |
| `option_groups` | group_id, dish_id, name, type, required, max_select | 口味选项组 |
| `option_items` | item_id, group_id, name, price_delta, available | 口味选项项 |
| `orders` | order_id, user_id, status, remark, created_at | 订单表 |
| `order_items` | id, order_id, dish_id, qty, unit_price | 订单明细表 |
| `order_item_options` | order_item_id, option_item_id | 订单项-选项关联表 |

---

## 🎨 UI 设计

- **色彩**: 渐变紫色主题（#667eea → #764ba2）
- **字体**: 系统默认 + PingFang SC
- **布局**: Flexbox + Grid 响应式布局
- **交互**: 悬浮效果、过渡动画、实时反馈

---

## 🚀 扩展建议

### 功能扩展

- [ ] 用户认证（JWT Token）
- [ ] 支付接口集成（微信/支付宝）
- [ ] 订单评价与星级
- [ ] 优惠券系统
- [ ] 数据统计看板

### 技术优化

- [ ] 使用 Redis 缓存菜品数据
- [ ] 使用 Celery 异步处理订单
- [ ] 使用 Nginx 反向代理
- [ ] 使用 Docker 容器化部署
- [ ] 使用 Alembic 数据库迁移

### 代码质量

- [ ] 增加单元测试覆盖率（目标 80%+）
- [ ] 使用 mypy 类型检查
- [ ] 使用 pre-commit 钩子
- [ ] CI/CD 流水线（GitHub Actions）

---

## 📝 开发规范

### 命名规范

- **文件名**: 小写+下划线（`order_service.py`）
- **类名**: 大驼峰（`OrderService`）
- **函数名**: 小写+下划线（`create_order`）
- **变量名**: 小写+下划线（`dish_id`）

### 提交规范

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试用例
chore: 构建/工具
```

---

## 📄 许可

MIT License

