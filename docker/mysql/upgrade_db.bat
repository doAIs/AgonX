@echo off
REM AgonX 数据库升级脚本 - v1.1 富媒体知识库
REM 使用方法: upgrade_db.bat

setlocal enabledelayedexpansion

echo ==========================================
echo AgonX 数据库升级工具 v1.1
echo ==========================================
echo.

REM 检测环境
docker ps 2>nul | findstr /C:"agonx-mysql" >nul
if %ERRORLEVEL% EQU 0 (
    set ENVIRONMENT=docker
    echo [32m√ 检测到 Docker 环境[0m
) else (
    mysql --version >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set ENVIRONMENT=local
        echo [32m√ 检测到本地 MySQL 环境[0m
    ) else (
        echo [31m× 未找到 MySQL 客户端或 Docker 环境[0m
        pause
        exit /b 1
    )
)

echo.
echo 【重要提示】
echo 1. 升级前会自动备份数据库
echo 2. 升级过程约需 1-2 秒
echo 3. 不影响现有数据和功能
echo.

set /p CONFIRM="确认开始升级？(y/N): "
if /i not "%CONFIRM%"=="y" (
    echo 已取消升级
    pause
    exit /b 0
)

echo.
echo ==========================================
echo 步骤 1/4: 备份数据库
echo ==========================================

for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set BACKUP_FILE=backup_%mydate%_%mytime%.sql

if "%ENVIRONMENT%"=="docker" (
    docker exec agonx-mysql mysqldump -u agonx -pagonx_password agonx > %BACKUP_FILE%
) else (
    mysqldump -h localhost -u agonx -pagonx_password agonx > %BACKUP_FILE%
)

echo [32m√ 备份完成: %BACKUP_FILE%[0m

echo.
echo ==========================================
echo 步骤 2/4: 执行升级脚本
echo ==========================================

set SCRIPT_DIR=%~dp0
set UPGRADE_SQL=%SCRIPT_DIR%upgrade_v1.1_rich_media.sql

if not exist "%UPGRADE_SQL%" (
    echo [31m× 升级脚本不存在: %UPGRADE_SQL%[0m
    pause
    exit /b 1
)

if "%ENVIRONMENT%"=="docker" (
    type "%UPGRADE_SQL%" | docker exec -i agonx-mysql mysql -u agonx -pagonx_password agonx
) else (
    mysql -h localhost -u agonx -pagonx_password agonx < "%UPGRADE_SQL%"
)

if %ERRORLEVEL% NEQ 0 (
    echo [31m× 升级脚本执行失败[0m
    pause
    exit /b 1
)

echo [32m√ 升级脚本执行完成[0m

echo.
echo ==========================================
echo 步骤 3/4: 验证升级结果
echo ==========================================

if "%ENVIRONMENT%"=="docker" (
    docker exec agonx-mysql mysql -u agonx -pagonx_password agonx -N -e "SHOW TABLES LIKE 'document_%%';" > temp_tables.txt
) else (
    mysql -h localhost -u agonx -pagonx_password agonx -N -e "SHOW TABLES LIKE 'document_%%';" > temp_tables.txt
)

echo 新增表:
for /f "tokens=*" %%i in (temp_tables.txt) do (
    echo   [32m√[0m %%i
)

del temp_tables.txt

echo.
echo ==========================================
echo 步骤 4/4: 完整性检查
echo ==========================================

set MISSING=0
for %%t in (document_pages document_elements document_chunks ocr_tasks) do (
    if "%ENVIRONMENT%"=="docker" (
        docker exec agonx-mysql mysql -u agonx -pagonx_password agonx -N -e "SHOW TABLES LIKE '%%t';" | findstr "%%t" >nul
    ) else (
        mysql -h localhost -u agonx -pagonx_password agonx -N -e "SHOW TABLES LIKE '%%t';" | findstr "%%t" >nul
    )
    if !ERRORLEVEL! NEQ 0 (
        echo [31m× 缺失表: %%t[0m
        set MISSING=1
    )
)

if %MISSING% EQU 1 (
    echo.
    echo [31m升级可能未完全成功，请查看日志[0m
    pause
    exit /b 1
)

echo [32m√ 所有表创建成功[0m

echo.
echo ==========================================
echo [32m√ 升级完成！[0m
echo ==========================================
echo.
echo 数据库版本: v1.1
echo 备份文件: %BACKUP_FILE%
echo.
echo 新增功能:
echo   • PDF 页面级管理
echo   • 图片自动提取
echo   • OCR 文字识别
echo   • 分块向量映射
echo   • 增强检索接口
echo.
echo 下一步:
echo   1. 重启后端服务: docker-compose restart backend
echo   2. 测试富媒体上传功能
echo   3. 查看详细验证: python backend\verify_migration.py
echo.

pause
