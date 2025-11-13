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


def call_gemini(prompt: str, base_url: str, api_key: str, model: str, size: str) -> dict:
    """
    兼容你提供的调用方式：
    curl http://14.103.68.46/v1/images/generations -H "Content-Type: application/json" -H "Authorization: Bearer $GEMINI_API_KEY" -d '{"model":"qwen-image","prompt":"红烧肉","n":1,"size":"1328*1328"}'
    """
    url = f"{base_url.rstrip('/')}/v1/images/generations"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "prompt": prompt, "n": 1, "size": size}
    resp = requests.post(url, json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    return resp.json()


def extract_image(data: dict) -> tuple[Optional[bytes], Optional[str]]:
    """
    解析API返回的图片数据：
    - 格式：{"data":[{"url":"..."}]} 或 {"data":[{"b64_json":"..."}]}
    - 返回：提取 data[0] 中的 url 或 b64_json
    """
    if not isinstance(data, dict) or "data" not in data:
        return None, None
    
    data_list = data.get("data")
    if not isinstance(data_list, list) or not data_list:
        return None, None
    
    # 取 data[0]
    first = data_list[0]
    if not isinstance(first, dict):
        return None, None
    
    # 优先检查 url（图片下载链接）
    if "url" in first and first["url"]:
        print(f"[INFO] 图片URL: {first['url']}")
        return None, first["url"]
    
    # 其次检查 b64_json（base64编码的图片）
    if "b64_json" in first and first["b64_json"]:
        try:
            return base64.b64decode(first["b64_json"]), None
        except Exception:
            return None, None
    
    return None, None


def download_image_from_url(url: str) -> bytes:
    """从URL下载图片"""
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    return resp.content


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
    parser.add_argument("--model", type=str, default=os.getenv("GEMINI_MODEL", "qwen-image"))
    parser.add_argument("--size", type=str, default=os.getenv("GEMINI_IMAGE_SIZE", "1328*1328"))
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
                data = call_gemini(prompt, args.base_url, args.api_key, args.model, args.size)
                print(f"[INFO] 图片数据: {data}")
                image_bytes, image_url = extract_image(data)
                
                # 如果返回的是base64编码的图片，直接保存
                if image_bytes:
                    image_url = save_local(image_bytes, f"dish_{dish.dish_id}.jpg")
                # 如果返回的是URL，下载图片后保存
                elif image_url:
                    print(f"[INFO] 下载图片 dish_id={dish.dish_id}, url={image_url}")
                    image_bytes = download_image_from_url(image_url)
                    image_url = save_local(image_bytes, f"dish_{dish.dish_id}.jpg")
                else:
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


