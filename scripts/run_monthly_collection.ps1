<#
Executa a coleta a partir da raiz do projeto. Use este arquivo como ação de uma
tarefa mensal do Agendador de Tarefas do Windows após validar `acoes-collect`.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Ambiente virtual não encontrado em $python"
}

Push-Location $projectRoot
try {
    & $python -m acoes_no_bolso.collect
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
finally {
    Pop-Location
}
