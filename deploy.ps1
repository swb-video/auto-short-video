# 全自动短视频变现系统 - PowerShell部署脚本
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  全自动短视频变现系统 - 一键部署脚本" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# 检查Git是否安装
try {
    $gitVersion = git --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Git not found"
    }
    Write-Host "Git已安装: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "错误: 未检测到Git，请先安装Git" -ForegroundColor Red
    Write-Host "下载地址: https://git-scm.com/download/win" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

# 设置工作目录
$projectDir = "c:\Users\41337\WorkBuddy\20260319083955"
Set-Location $projectDir

Write-Host ""
Write-Host "[1/5] 正在初始化Git仓库..." -ForegroundColor Cyan
git init
if ($LASTEXITCODE -ne 0) {
    Write-Host "Git初始化失败" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

git config user.name "swb-video"
git config user.email "deploy@auto-short.video"

Write-Host "[2/5] 正在添加文件到Git..." -ForegroundColor Cyan
git add .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Git添加失败" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host "[3/5] 正在提交代码..." -ForegroundColor Cyan
git commit -m "Initial commit"
if ($LASTEXITCODE -ne 0) {
    Write-Host "提交失败，可能已有提交或无变更" -ForegroundColor Yellow
}

Write-Host "[4/5] 正在连接到GitHub仓库..." -ForegroundColor Cyan
git branch -M main
git remote remove origin 2>$null
git remote add origin https://github.com/swb-video/auto-short-video.git

Write-Host "[5/5] 正在推送代码到GitHub..." -ForegroundColor Cyan
git push -u origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "推送失败，请检查：" -ForegroundColor Red
    Write-Host "1. 是否已登录GitHub账号" -ForegroundColor Yellow
    Write-Host "2. 网络连接是否正常" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "解决方法：" -ForegroundColor Cyan
    Write-Host "- 在浏览器中访问 https://github.com 确保已登录" -ForegroundColor White
    Write-Host "- 重新运行此脚本" -ForegroundColor White
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  部署成功！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor Cyan
Write-Host "1. 访问: https://github.com/swb-video/auto-short-video" -ForegroundColor White
Write-Host "2. 点击 Settings - Secrets and variables - Actions" -ForegroundColor White
Write-Host "3. 添加5个Secrets" -ForegroundColor White
Write-Host ""
Write-Host "按回车键打开GitHub仓库页面..." -ForegroundColor Yellow
Read-Host
Start-Process "https://github.com/swb-video/auto-short-video"
