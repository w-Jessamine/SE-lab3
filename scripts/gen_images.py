#!/usr/bin/env python3
"""
独立的“批量生成菜品图片”脚本（与应用解耦）

使用：
  export GEMINI_BASE_URL=http://14.103.68.46
  export GEMINI_API_KEY=xxxxx
  python scripts/gen_images.py --force
  python scripts/gen_images.py --ids 1,2,3
"""
from __future__ import annotations
import argparse
import base64
import os
import pathlib
import sys
from typing import Iterable, Optional, List
import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db import SessionLocal  # noqa: E402
from app.models.dish import Dish  # noqa: E402


def prompt_for_dish(dish: Dish) -> str:
    return f"美食照片，菜品：{dish.name}，中餐家常风格，高质感，自然光，浅景深，简洁白盘。"


def ensure_out_dir() -> pathlib.Path:
    out_dir = ROOT / "app" / "static" / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def call_gemini(prompt: str, base_url: str, api_key: str) -> dict:
    url = f"{base_url.rstrip('/')}/v1beta/models/gemini-2.5-flash-image:generateContent"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()


def extract_image(data: dict) -> tuple[Optional[bytes], Optional[str]]:
    # 优先拿直链
    if isinstance(data, dict) and "image_url" in data:
        return None, data["image_url"]
    # 兼容 base64 的常见结构（需按实际接口调整）
    try:
        cand = data.get("candidates", [])[0]
        parts = cand.get("content", {}).get("parts", [])
        inline = next((p for p in parts if "inline_data" in p), None)
        if inline:
            b64 = inline["inline_data"]["data"]
            return base64.b64decode(b64), None
    except Exception:
        pass
    return None, None


def save_local(image_bytes: bytes, filename: str) -> str:
    out_dir = ensure_out_dir()
    path = out_dir / filename
    with open(path, "wb") as f:
        f.write(image_bytes)
    return f"/static/images/{filename}"


def main():
    parser = argparse.ArgumentParser(description="批量生成菜品图片并写入数据库 image_url")
    parser.add_argument("--ids", type=str, default="", help="指定菜品ID，逗号分隔")
    parser.add_argument("--force", action="store_true", help="即使已有图片也覆盖生成")
    parser.add_argument("--dry", action="store_true", help="只打印，不写入")
    parser.add_argument("--base-url", type=str, default=os.getenv("GEMINI_BASE_URL", ""))
    parser.add_argument("--api-key", type=str, default=os.getenv("GEMINI_API_KEY", ""))
    args = parser.parse_args()

    if not args.base_url or not args.api_key:
        print("缺少 GEMINI_BASE_URL 或 GEMINI_API_KEY", file=sys.stderr)
        sys.exit(2)

    session = SessionLocal()
    try:
        query = session.query(Dish)
        ids = [int(x) for x in args.ids.split(",") if x.strip()] if args.ids else []
        if ids:
            query = query.filter(Dish.dish_id.in_(ids))
        elif not args.force:
            query = query.filter((Dish.image_url == "") | (Dish.image_url.is_(None)))
        dishes: List[Dish] = query.all()

        updated = 0
        for dish in dishes:
            prompt = prompt_for_dish(dish)
            try:
                data = call_gemini(prompt, args.base_url, args.api_key)
                image_bytes, image_url = extract_image(data)
                if image_bytes:
                    image_url = save_local(image_bytes, f"dish_{dish.dish_id}.jpg")
                if not image_url:
                    print(f"[WARN] 无有效图片返回 dish_id={dish.dish_id}")
                    continue
                print(f"[OK] {dish.dish_id} -> {image_url}")
                if not args.dry:
                    dish.image_url = image_url
                    updated += 1
            except Exception as e:
                print(f"[ERR] dish_id={dish.dish_id}: {e}")
        if not args.dry:
            session.commit()
        print(f"完成，更新 {updated} 个菜品。")
    finally:
        session.close()


if __name__ == "__main__":
    main()


