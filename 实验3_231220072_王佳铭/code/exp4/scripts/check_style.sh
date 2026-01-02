#!/bin/bash
# 代码风格检查脚本

set -e

echo "🔍 开始代码风格检查..."
echo ""

# Black 检查
echo "1️⃣  Running Black..."
python -m black --check app/ || {
    echo "❌ Black 检查失败！运行 'black app/' 自动修复"
    exit 1
}
echo "✅ Black 检查通过"
echo ""

# Ruff 检查
echo "2️⃣  Running Ruff..."
python -m ruff check app/ || {
    echo "❌ Ruff 检查失败！运行 'ruff check app/ --fix' 自动修复"
    exit 1
}
echo "✅ Ruff 检查通过"
echo ""

# Pylint 检查（忽略部分规则）
echo "3️⃣  Running Pylint..."
python -m pylint app/ \
    --disable=C0111,R0903,C0103,R0801,R0913 \
    --max-line-length=100 \
    --ignore=pages || {
    echo "⚠️  Pylint 有警告（可忽略）"
}
echo "✅ Pylint 检查完成"
echo ""

echo "🎉 所有检查通过！"

