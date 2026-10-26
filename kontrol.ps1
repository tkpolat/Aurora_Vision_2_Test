Set-Location $PSScriptRoot
& .\.venv\Scripts\python.exe -m py_compile app.py
if ($LASTEXITCODE -ne 0) { Write-Host 'SOZDIZIMI HATASI' -ForegroundColor Red; exit 1 }
Write-Host 'OK - uygulama aciliyor' -ForegroundColor Green
& .\.venv\Scripts\python.exe app.py
