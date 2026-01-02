"""FastAPI 应用入口"""
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.db import init_db
from app.api import auth, menu, order, admin
from fastapi import Request

# 创建 FastAPI 应用
app = FastAPI(
    title="点单程序网",
    description="基于 FastAPI + SQLAlchemy 的点单系统（不涉及支付）",
    version="1.0.0"
)

# 挂载路由
app.include_router(auth.router)
app.include_router(menu.router)
app.include_router(order.router)
app.include_router(admin.router)

# 配置模板
templates = Jinja2Templates(directory="app/pages")
# 静态资源（用于菜品图片）
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def on_startup():
    """启动时初始化数据库"""
    init_db()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """渲染主页（菜品浏览）"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/checkout", response_class=HTMLResponse)
async def checkout_page(request: Request):
    """渲染下单确认页"""
    return templates.TemplateResponse("checkout.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """渲染后台管理页"""
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/order/{order_id}", response_class=HTMLResponse)
async def order_detail_page(request: Request, order_id: int):
    """渲染订单详情页（JS 调用 API 获取数据）"""
    return templates.TemplateResponse("order_detail.html", {"request": request})

@app.get("/health")
def health_check():
    """健康检查接口"""
    return {"status": "ok"}

@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """调试页面"""
    with open("test_frontend.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

