# 🍽️ 点单程序网

基于 **Python + FastAPI + SQLAlchemy + Jinja2** 的最小可用点单系统（单体Web应用）

## 📋 项目说明

这是一个**仅处理点单信息**的餐饮订单管理系统，**不涉及在线支付功能**。用户下单后需线下付款。

### 核心功能

- ✅ **用户管理**：简化登录（游客/注册用户），区分普通用户与管理员
- ✅ **菜品浏览**：按分类展示菜品，分页查询，实时显示库存状态
- ✅ **口味选项**：支持单选/多选配置（辣度、分量、加料等）
- ✅ **库存管理**：下单时同步扣减库存，使用事务保证一致性
- ✅ **订单流程**：Created → Submitted → Completed/Cancelled
- ✅ **后台管理**：菜品上下架、库存调整、订单查看
- ✅ **并发控制**：使用 `SELECT ... FOR UPDATE` 防止超卖

### 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| Web 框架 | FastAPI | 0.109.0 |
| ORM | SQLAlchemy | 2.0.25 |
| 数据验证 | Pydantic | 2.5.3 |
| 模板引擎 | Jinja2 | 3.1.3 |
| 数据库 | SQLite / MySQL | - |
| 测试 | pytest | 7.4.4 |

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
# 运行种子数据脚本（自动创建表并插入样例数据）
python scripts/seed.py
```

**默认数据：**
- 管理员账号：`admin`
- 5个分类：特色菜、肉类、素菜、酒水、主食
- 20道菜品，部分配置口味选项
- 3个口味选项组（辣度、分量、加料）

### 3. 启动服务

```bash
# 开发模式（热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问应用

| 页面 | 地址 | 说明 |
|------|------|------|
| 前台主页 | http://localhost:8000/ | 菜品浏览与点单 |
| 下单确认 | http://localhost:8000/checkout | 确认订单并提交 |
| 后台管理 | http://localhost:8000/admin | 管理菜品、库存、订单 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| 健康检查 | http://localhost:8000/health | 服务状态 |

## 📱 界面特性

- ✨ **响应式设计**：自适应电脑和手机屏幕
- 🎨 **现代UI**：渐变色背景、卡片式布局、流畅动画
- 🛒 **购物车**：悬浮购物车图标，实时显示商品数量
- 📊 **直观管理**：后台Tab切换，表格展示订单数据

## 🧪 测试

### 运行所有测试

```bash
pytest -v
```

### 测试覆盖

- ✅ 库存校验测试（`test_inventory.py`）
  - 库存充足/不足
  - 菜品上下架状态
  - 库存调整（正负值）
  
- ✅ 订单业务测试（`test_order.py`）
  - 正常下单成功
  - 库存不足失败
  - 菜品下架失败
  - 订单取消/完成
  - 带口味选项的订单
  
- ✅ 并发测试（`test_concurrency.py`）
  - 防止超卖（两用户同时下单有限库存）
  - 顺序下单对比

## 🛠️ 开发工具

### 代码风格检查

```bash
# 运行所有检查（Black + Ruff + Pylint）
bash scripts/check_style.sh

# 或单独运行
black app/                    # 格式化代码
ruff check app/ --fix         # 自动修复 linter 问题
pylint app/ --disable=C0111   # 代码质量检查
```

### 统计代码行数

```bash
bash scripts/count_lines.sh
```

**预期输出：** 核心业务代码 500-1000 行（不含模板、测试）

## 📂 项目结构

```
lab3/
├── app/
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 配置管理
│   ├── db.py                   # 数据库会话
│   │
│   ├── models/                 # SQLAlchemy ORM 模型
│   │   ├── enums.py            # 枚举类型
│   │   ├── user.py             # 用户模型
│   │   ├── dish.py             # 菜品、分类、选项
│   │   └── order.py            # 订单、订单项
│   │
│   ├── schemas/                # Pydantic DTO
│   │   ├── user.py
│   │   ├── dish.py
│   │   ├── option.py
│   │   └── order.py
│   │
│   ├── services/               # 业务逻辑层
│   │   ├── menu_service.py
│   │   ├── inventory_service.py
│   │   └── order_service.py
│   │
│   ├── api/                    # 路由层
│   │   ├── auth.py             # 登录
│   │   ├── menu.py             # 菜品浏览
│   │   ├── order.py            # 订单管理
│   │   └── admin.py            # 后台管理
│   │
│   └── pages/                  # Jinja2 模板
│       ├── index.html          # 主页
│       ├── checkout.html       # 下单页
│       └── admin.html          # 后台页
│
├── tests/                      # 测试用例
│   ├── conftest.py
│   ├── test_inventory.py
│   ├── test_order.py
│   └── test_concurrency.py
│
├── scripts/
│   ├── seed.py                 # 数据初始化
│   ├── check_style.sh          # 风格检查
│   └── count_lines.sh          # 代码统计
│
├── UML/                        # UML 设计图
│   ├── 类图.puml
│   ├── 序列图.puml
│   ├── 用例图.puml
│   └── 组件图.puml
│
├── requirements.txt
├── README.md
└── .gitignore
```

## 🔧 配置说明

### 数据库配置

默认使用 SQLite（开发环境）：

```python
# app/config.py
DATABASE_URL = "sqlite:///./order_system.db"
```

切换到 MySQL（生产环境）：

```python
DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/order_db"
```

### 并发安全说明

- **MySQL**：使用 `SELECT ... FOR UPDATE` 行锁防止超卖
- **SQLite**：使用 `serializable` 事务隔离级别（单线程限制）

## 📊 核心业务逻辑

### 订单创建流程

```python
def create_order(dto: OrderCreate) -> OrderResponse:
    """
    事务边界：
      1. 开启事务
      2. 对涉及的 Dish 行加锁（SELECT ... FOR UPDATE）
      3. 校验：status==OnShelf AND stock >= qty
      4. 计算总价（dish.price + sum(option.price_delta)) * qty
      5. 扣减库存
      6. 插入 orders、order_items、order_item_options
      7. 提交事务
    
    异常：菜品下架/库存不足/选项不可用 -> 回滚
    """
```

### 库存管理

- `Dish.is_available()`: 判断 `status==OnShelf AND stock > 0`
- `Dish.update_stock(delta)`: 调整库存（可正可负）
- 下单时同步扣减，取消订单**不退库存**

## 🎯 使用场景

### 顾客点单流程

1. 访问首页，浏览菜品（可作为游客或注册用户）
2. 按分类筛选，查看实时库存状态
3. 添加菜品到购物车，配置口味选项
4. 进入下单页面，填写备注
5. 提交订单（系统返回订单号和总价）
6. **线下付款**

### 商家后台操作

1. 使用管理员账号（`admin`）登录
2. 访问后台管理页面 `/admin`
3. **库存管理**：
   - 调整菜品库存（输入菜品ID和调整量）
   - 上下架菜品
4. **订单管理**：
   - 查看所有订单
   - 按状态筛选（已提交/已完成/已取消）
   - 完成订单（将状态从 Submitted 改为 Completed）

## ⚠️ 重要说明

1. **不涉及支付**：系统仅处理订单信息，不包含在线支付功能。订单生成后需线下付款。
2. **库存扣减时机**：下单成功即扣减库存，取消订单不退库存（避免恶意下单）。
3. **并发限制**：SQLite 在高并发下可能出现 `database is locked` 错误，生产环境建议使用 MySQL。
4. **权限控制**：本演示未实现完整的权限验证，后台接口应添加管理员权限校验。

## 📄 API 文档

启动服务后访问 http://localhost:8000/docs 查看完整 API 文档（Swagger UI）

### 主要接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/login` | POST | 假登录（创建或返回用户） |
| `/api/categories` | GET | 获取所有分类 |
| `/api/dishes` | GET | 分页查询菜品 |
| `/api/dishes/{id}/options` | GET | 获取菜品口味选项 |
| `/api/stock?dish_id=` | GET | 查询实时库存 |
| `/api/orders` | POST | 创建订单 |
| `/api/orders/{id}` | GET | 查询订单详情 |
| `/api/orders/{id}/cancel` | POST | 取消订单 |
| `/api/admin/dishes/{id}/status` | PATCH | 上下架菜品 |
| `/api/admin/inventory/adjust` | POST | 调整库存 |
| `/api/admin/orders` | GET | 查看所有订单 |
| `/api/admin/orders/{id}/complete` | POST | 完成订单 |

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📝 许可

MIT License

