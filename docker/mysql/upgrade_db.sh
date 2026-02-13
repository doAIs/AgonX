#!/bin/bash
# AgonX 数据库升级脚本 - v1.1 富媒体知识库
# 使用方法: ./upgrade_db.sh

set -e  # 遇到错误立即退出

echo "=========================================="
echo "AgonX 数据库升级工具 v1.1"
echo "=========================================="
echo ""

# 检测环境
if command -v docker &> /dev/null && docker ps | grep -q agonx-mysql; then
    ENVIRONMENT="docker"
    echo "✓ 检测到 Docker 环境"
elif command -v mysql &> /dev/null; then
    ENVIRONMENT="local"
    echo "✓ 检测到本地 MySQL 环境"
else
    echo "✗ 未找到 MySQL 客户端或 Docker 环境"
    exit 1
fi

echo ""
echo "【重要提示】"
echo "1. 升级前会自动备份数据库"
echo "2. 升级过程约需 1-2 秒"
echo "3. 不影响现有数据和功能"
echo ""

# 询问确认
read -p "确认开始升级？(y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消升级"
    exit 0
fi

echo ""
echo "=========================================="
echo "步骤 1/4: 备份数据库"
echo "=========================================="

BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"

if [ "$ENVIRONMENT" = "docker" ]; then
    docker exec agonx-mysql mysqldump -u agonx -pagonx_password agonx > "$BACKUP_FILE"
else
    mysqldump -h localhost -u agonx -pagonx_password agonx > "$BACKUP_FILE"
fi

echo "✓ 备份完成: $BACKUP_FILE"

echo ""
echo "=========================================="
echo "步骤 2/4: 执行升级脚本"
echo "=========================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPGRADE_SQL="$SCRIPT_DIR/upgrade_v1.1_rich_media.sql"

if [ ! -f "$UPGRADE_SQL" ]; then
    echo "✗ 升级脚本不存在: $UPGRADE_SQL"
    exit 1
fi

if [ "$ENVIRONMENT" = "docker" ]; then
    docker exec -i agonx-mysql mysql -u agonx -pagonx_password agonx < "$UPGRADE_SQL"
else
    mysql -h localhost -u agonx -pagonx_password agonx < "$UPGRADE_SQL"
fi

echo "✓ 升级脚本执行完成"

echo ""
echo "=========================================="
echo "步骤 3/4: 验证升级结果"
echo "=========================================="

if [ "$ENVIRONMENT" = "docker" ]; then
    TABLES=$(docker exec agonx-mysql mysql -u agonx -pagonx_password agonx -N -e "SHOW TABLES LIKE 'document_%';")
else
    TABLES=$(mysql -h localhost -u agonx -pagonx_password agonx -N -e "SHOW TABLES LIKE 'document_%';")
fi

echo "新增表:"
echo "$TABLES" | while read table; do
    echo "  ✓ $table"
done

echo ""
echo "=========================================="
echo "步骤 4/4: 完整性检查"
echo "=========================================="

EXPECTED_TABLES=("document_pages" "document_elements" "document_chunks" "ocr_tasks")
MISSING_TABLES=()

for table in "${EXPECTED_TABLES[@]}"; do
    if ! echo "$TABLES" | grep -q "^$table$"; then
        MISSING_TABLES+=("$table")
    fi
done

if [ ${#MISSING_TABLES[@]} -eq 0 ]; then
    echo "✓ 所有表创建成功"
else
    echo "✗ 缺失以下表:"
    for table in "${MISSING_TABLES[@]}"; do
        echo "  - $table"
    done
    echo ""
    echo "升级可能未完全成功，请查看日志"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 升级完成！"
echo "=========================================="
echo ""
echo "数据库版本: v1.1"
echo "备份文件: $BACKUP_FILE"
echo ""
echo "新增功能:"
echo "  • PDF 页面级管理"
echo "  • 图片自动提取"
echo "  • OCR 文字识别"
echo "  • 分块向量映射"
echo "  • 增强检索接口"
echo ""
echo "下一步:"
echo "  1. 重启后端服务: docker-compose restart backend"
echo "  2. 测试富媒体上传功能"
echo "  3. 查看详细验证: python backend/verify_migration.py"
echo ""
