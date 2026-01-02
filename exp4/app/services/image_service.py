"""菜品图片生成服务（Gemini）"""
from __future__ import annotations
import os
import pathlib
from typing import Optional, Iterable
import requests
from app.config import settings
from app.models.dish import Dish
from sqlalchemy.orm import Session


class ImageService:
    """封装与外部 AI 图片服务交互"""

    def __init__(self, db: Session):
        self.db = db
        self.base_url = settings.GEMINI_BASE_URL
        self.api_key = settings.GEMINI_API_KEY
        # 静态目录
        self.static_dir = pathlib.Path("app/static/images")
        self.static_dir.mkdir(parents=True, exist_ok=True)

    def _prompt_for_dish(self, dish: Dish) -> str:
        return f"美食摄影，菜品：{dish.name}，中国家常菜风格，高质感，自然光，白色盘子，浅景深。"

    def generate_image_for_dish(self, dish: Dish, force: bool = False) -> Optional[str]:
        """
        为单个菜品生成图片并保存到本地静态目录，返回可访问URL。
        若 image_url 已存在且非 force，则跳过返回原值。
        """
        if not self.base_url or not self.api_key:
            raise RuntimeError("未配置 GEMINI_BASE_URL 或 GEMINI_API_KEY")

        if dish.image_url and not force:
            return dish.image_url

        prompt = self._prompt_for_dish(dish)
        url = f"{self.base_url}/v1beta/models/gemini-2.5-flash-image:generateContent"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            # 一些服务需要 extra params，可按实际 API 调整
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        # 兼容两种返回：直接URL 或 base64
        image_bytes: Optional[bytes] = None
        image_url: Optional[str] = None

        # 假设返回 data["image_url"]
        if isinstance(data, dict) and "image_url" in data:
            image_url = data["image_url"]
        else:
            # 示例：如果返回 base64
            # b64 = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("inline_data", {}).get("data")
            b64 = None
            if b64:
                import base64

                image_bytes = base64.b64decode(b64)

        if image_bytes:
            filename = f"dish_{dish.dish_id}.jpg"
            path = self.static_dir / filename
            with open(path, "wb") as f:
                f.write(image_bytes)
            return f"/static/images/{filename}"

        return image_url

    def batch_generate_for_dishes(self, dishes: Iterable[Dish], force: bool = False) -> int:
        """为一批菜品生成图片，返回成功数量"""
        ok = 0
        for dish in dishes:
            try:
                url = self.generate_image_for_dish(dish, force=force)
                if url:
                    dish.image_url = url
                    ok += 1
            except Exception:
                # 不中断批处理
                continue
        self.db.commit()
        return ok


