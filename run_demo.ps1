param([int]$Port = 8501)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:PYTHONIOENCODING = 'utf-8'
$env:OMP_NUM_THREADS = '2'
$env:MKL_NUM_THREADS = '2'
$env:OPENBLAS_NUM_THREADS = '2'
if (Test-Path -LiteralPath '.venv/Scripts/python.exe') {
    & '.venv/Scripts/python.exe' -m streamlit run app/streamlit_app.py --global.developmentMode=false --server.port $Port --server.address 127.0.0.1
} else {
    $env:PYTHONPATH = "$PSScriptRoot/.deps;$PSScriptRoot"
    & python -m streamlit run app/streamlit_app.py --global.developmentMode=false --server.port $Port --server.address 127.0.0.1
}
