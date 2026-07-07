Write-Host ""
Write-Host "========================================="
Write-Host "      ACD QUALITY GATE"
Write-Host "========================================="
Write-Host ""

Write-Host "[1/5] Black"
black --check .

Write-Host ""
Write-Host "[2/5] Ruff"
ruff check .

Write-Host ""
Write-Host "[3/5] Pytest"
pytest

Write-Host ""
Write-Host "[4/5] Architecture Inventory"
python acd/tools/architecture_inventory.py

Write-Host ""
Write-Host "[5/5] Inicialização do ACD"

python app.py

Write-Host ""
Write-Host "========================================="
Write-Host "QUALITY GATE FINALIZADO"
Write-Host "========================================="