#!/bin/bash
# 统计核心代码行数（不含模板和测试）

echo "📊 统计核心业务代码行数..."
echo ""

# 检查是否安装 cloc
if ! command -v cloc &> /dev/null; then
    echo "⚠️  未安装 cloc，使用 wc 统计"
    echo ""
    
    echo "Models:"
    find app/models -name "*.py" -type f | xargs wc -l | tail -1
    
    echo "Schemas:"
    find app/schemas -name "*.py" -type f | xargs wc -l | tail -1
    
    echo "Services:"
    find app/services -name "*.py" -type f | xargs wc -l | tail -1
    
    echo "API:"
    find app/api -name "*.py" -type f | xargs wc -l | tail -1
    
    echo "Database & Config:"
    wc -l app/db.py app/config.py app/main.py | tail -1
    
    echo ""
    echo "总计（不含测试和模板）:"
    find app -name "*.py" -not -path "*/pages/*" | xargs wc -l | tail -1
else
    # 使用 cloc 统计
    cloc app/ \
        --exclude-dir=pages \
        --include-lang=Python \
        --by-file-by-lang
    
    echo ""
    echo "核心业务代码统计（Python，不含模板）:"
    cloc app/ \
        --exclude-dir=pages \
        --include-lang=Python
fi

echo ""
echo "💡 目标：核心代码 500-1000 行"

