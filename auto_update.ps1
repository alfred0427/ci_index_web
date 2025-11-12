# ======== Lite 多市場自動更新器 ========

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
cd $PSScriptRoot
$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm'

# 🏦 定義要更新的市場（可自行增減）
$markets = @('TW','US','JP')


foreach ($m in $markets) {
    Write-Host "🚀 Running main.py for $m..."
    python main.py fscore --market $m

    Write-Host "📦 Adding updated files for $m..."
    git add "${m}_buy_data/" "${m}_sell_data/"
}

# 若沒有變更則略過
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "⚠️ No changes to commit."
} else {
    $msg = "auto update $timestamp"
    git commit -m $msg
    git push origin main
    Write-Host "✅ Successfully pushed changes to GitHub."
}

# 打開 index copy.html（預設 TW 市場）
$indexPath = Join-Path $PSScriptRoot "index copy.html"
if (Test-Path $indexPath) {
    Write-Host "🌐 Opening index copy.html (TW market)..."
    Start-Process $indexPath
} else {
    Write-Host "⚠️ index copy.html not found!"
}
Write-Host "🎉 Done!"
