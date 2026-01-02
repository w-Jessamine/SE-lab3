# ⚡ 快速启动指南

本文档提供最快的方式启动"点单程序网"项目。

## 📦 一键安装与启动

```bash
# 1. 进入项目目录
cd /Users/w_jasmine/code/lab3

# 2. 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库（自动创建表和样例数据）
python scripts/seed.py

# 5. 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问：
- 🏠 **前台主页**：http://localhost:8000/
- 🛠️ **后台管理**：http://localhost:8000/admin
- 📖 **API 文档**：http://localhost:8000/docs

## 🧪 运行测试

```bash
# 运行所有测试
pytest -v

# 运行特定测试
pytest tests/test_inventory.py -v
pytest tests/test_order.py -v
pytest tests/test_concurrency.py -v
```

## 🎯 快速验证功能

### 前台点单流程

1. 访问 http://localhost:8000/
2. 输入用户名登录（如 `张三`）或跳过作为游客
3. 浏览菜品，点击 `+` 按钮添加到购物车
4. 点击右下角浮动购物车按钮
5. 填写备注，提交订单
6. 系统返回订单号和总价

### 后台管理验证

1. 访问 http://localhost:8000/admin
2. 在**库存管理**标签：
   - 输入菜品ID（如 `1`）和调整量（如 `10`）
   - 点击"调整库存"
3. 在**订单管理**标签：
   - 查看所有订单
   - 对"已提交"状态的订单点击"完成"按钮

### API 测试（使用 curl）

```bash
# 1. 登录/注册
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser"}'

# 2. 获取分类
curl http://localhost:8000/api/categories

# 3. 获取菜品列表
curl http://localhost:8000/api/dishes

# 4. 查询库存
curl "http://localhost:8000/api/stock?dish_id=1"

# 5. 创建订单
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "remark": "不要辣",
    "items": [
      {"dish_id": 1, "qty": 2, "option_item_ids": []},
      {"dish_id": 2, "qty": 1, "option_item_ids": []}
    ]
  }'
```

## 📊 代码统计

```bash
# 统计核心业务代码行数
bash scripts/count_lines.sh
```

**实际统计结果：** 约 **1185 行** Python 代码（包含所有模块）

按模块分布：
- Models（数据模型）：~200 行
- Services（业务逻辑）：~400 行
- API（路由层）：~250 行
- Schemas（DTO）：~150 行
- 配置与入口：~50 行
- 测试用例：~350 行

## 🔍 代码检查

```bash
# 运行所有风格检查
bash scripts/check_style.sh

# 或单独运行
black app/                # 格式化
ruff check app/ --fix     # 修复 linter 问题
```

## 📱 测试移动端

启动服务后，用手机浏览器访问（确保手机和电脑在同一网络）：

```
http://YOUR_COMPUTER_IP:8000/
```

查找电脑IP：
- macOS/Linux: `ifconfig | grep "inet "`
- Windows: `ipconfig`

## 🗄️ 数据库说明

### 默认数据

初始化后包含：
- 👤 **用户**：1 个管理员（`admin`）
- 📂 **分类**：5 个（特色菜、肉类、素菜、酒水、主食）
- 🍽️ **菜品**：20 道
- 🌶️ **口味选项**：3 组（辣度、分量、加料）

### 清空数据库

```bash
# 删除数据库文件
rm order_system.db

# 重新初始化
python scripts/seed.py
```

## 🐛 常见问题

### 1. 端口被占用

```bash
# 使用其他端口
uvicorn app.main:app --reload --port 8080
```

### 2. 模块导入错误

```bash
# 确认在项目根目录运行
pwd  # 应显示 .../lab3

# 确认虚拟环境已激活
which python  # 应显示 venv/bin/python
```

### 3. 数据库锁定（SQLite 并发限制）

SQLite 不适合高并发，生产环境建议使用 MySQL：

```python
# 修改 app/config.py
DATABASE_URL = "mysql+pymysql://user:pass@localhost/order_db"
```

### 4. 测试失败

```bash
# 清空测试缓存
rm -rf .pytest_cache

# 重新运行
pytest -v --tb=short
```

## 📚 下一步

- ✅ 查看 `README.md` 了解完整功能
- ✅ 查看 `GIT_REMOTE_SETUP.md` 托管到远程仓库
- ✅ 查看 `http://localhost:8000/docs` 浏览 API 文档
- ✅ 修改 `app/pages/` 下的模板自定义UI

## 🎉 快速演示脚本

```bash
#!/bin/bash
# 一键演示脚本

echo "🚀 启动点单程序网演示..."

# 安装依赖（如果尚未安装）
pip install -q -r requirements.txt

# 初始化数据库
echo "📦 初始化数据库..."
python scripts/seed.py

# 启动服务
echo "🔥 启动服务（Ctrl+C 退出）..."
echo "📱 前台：http://localhost:8000/"
echo "🛠️ 后台：http://localhost:8000/admin"
echo "📖 文档：http://localhost:8000/docs"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

保存为 `demo.sh`，运行 `bash demo.sh` 即可快速演示！

