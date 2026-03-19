@echo off
chcp 65001 >nul
echo ==========================================
echo  全自动短视频变现系统 - 一键部署脚本
echo ==========================================
echo.

REM 检查Git是否安装
git --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Git，请先安装Git
    echo 下载地址: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [1/5] 正在初始化Git仓库...
git init
git config user.name "swb-video"
git config user.email "deploy@auto-short.video"

echo [2/5] 正在添加文件到Git...
git add .

echo [3/5] 正在提交代码...
git commit -m "Initial commit: 全自动短视频变现系统"

echo [4/5] 正在连接到GitHub仓库...
git branch -M main
git remote add origin https://github.com/swb-video/auto-short-video.git

echo [5/5] 正在推送代码到GitHub...
git push -u origin main

if errorlevel 1 (
    echo.
    echo [错误] 推送失败，请检查：
    echo 1. 是否已登录GitHub账号
    echo 2. 网络连接是否正常
    echo.
    echo 解决方法：
    echo - 在浏览器中确保已登录GitHub
    echo - 重新运行此脚本
    pause
    exit /b 1
)

echo.
echo ==========================================
echo  ✅ 部署成功！
echo ==========================================
echo.
echo 下一步操作：
echo 1. 访问: https://github.com/swb-video/auto-short-video
echo 2. 点击 Settings ^> Secrets and variables ^> Actions
echo 3. 添加以下Secrets：
echo    - DEEPSEEK_API_KEY
echo    - FEISHU_APP_ID
echo    - FEISHU_APP_SECRET
echo    - FEISHU_APP_TOKEN
echo    - FEISHU_TABLE_ID
echo.
echo 按任意键打开GitHub仓库页面...
pause >nul
start https://github.com/swb-video/auto-short-video
