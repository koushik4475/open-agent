# ================================================================
# scripts/setup_windows.ps1
# Windows setup script for OpenAgent
# Run this ONCE before starting the agent
# ================================================================

Write-Host "=============================================="
Write-Host "  OpenAgent — Windows Setup Script"
Write-Host "=============================================="
Write-Host ""

# ─── 1. Check if Ollama is installed ──────────────────────────
Write-Host "Checking for Ollama installation..."
$ollamaInstalled = $false

try {
    $ollamaVersion = ollama --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Ollama is already installed." -ForegroundColor Green
        Write-Host "   Version: $ollamaVersion"
        $ollamaInstalled = $true
    }
}
catch {
    $ollamaInstalled = $false
}

if (-not $ollamaInstalled) {
    # Check default path just in case
    if (Test-Path "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe") {
        Write-Host "✅ Ollama found at default path." -ForegroundColor Green
        $ollamaInstalled = $true
        # Add to path for this session
        $env:Path += ";$env:LOCALAPPDATA\Programs\Ollama"
    }
    else {
        Write-Host "❌ Ollama not found." -ForegroundColor Red
        Write-Host ""
        Write-Host "📥 Please install Ollama manually:" -ForegroundColor Yellow
        Write-Host "   1. Download from: https://ollama.ai/download/windows"
        Write-Host "   2. Run the installer"
        Write-Host "   3. Restart this script"
        Write-Host ""
        exit 1
    }
}

Write-Host ""

# ─── 2. Check if Ollama service is running ────────────────────
Write-Host "Checking Ollama service status..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
    Write-Host "✅ Ollama service is running." -ForegroundColor Green
}
catch {
    Write-Host "⚠️  Ollama service seems down. It should auto-start." -ForegroundColor Yellow
    Write-Host "   Try running 'ollama serve' in a separate terminal if needed."
    Start-Sleep -Seconds 3
}

Write-Host ""

# ─── 3. Pull the primary model ────────────────────────────────
$PRIMARY_MODEL = "phi3:mini"
Write-Host "📥 Pulling primary model: $PRIMARY_MODEL" -ForegroundColor Cyan
Write-Host "   Size: ~2.5 GB | License: MIT"
Write-Host "   This may take a few minutes on first run..."
Write-Host ""

# Use direct path if command fails
$ollamaCmd = "ollama"
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    $ollamaCmd = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
}

try {
    & $ollamaCmd pull $PRIMARY_MODEL
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Model '$PRIMARY_MODEL' downloaded successfully." -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  Pull failed. Check internet connection." -ForegroundColor Yellow
    }
}
catch {
    Write-Host "⚠️  Error invoking ollama pull: $_" -ForegroundColor Red
}

Write-Host ""

# ─── 4. Check Tesseract OCR ────────────────────────────────────
Write-Host "Checking for Tesseract OCR..."
$tesseractInstalled = $false

try {
    $tesseractVersion = tesseract --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Tesseract OCR is installed." -ForegroundColor Green
        $tesseractInstalled = $true
    }
}
catch {
    $tesseractInstalled = $false
}

if (-not $tesseractInstalled) {
    Write-Host "❌ Tesseract OCR not found." -ForegroundColor Red
    Write-Host "   (Optional) Install for image text extraction features."
}

Write-Host ""

Write-Host "=============================================="
Write-Host "  ✅ Setup complete!" -ForegroundColor Green
Write-Host "=============================================="
