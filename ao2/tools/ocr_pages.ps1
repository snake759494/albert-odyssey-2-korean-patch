param([string]$InputDirectory, [string]$OutputDirectory)
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$pageCount = 0
Get-ChildItem -LiteralPath $InputDirectory -Filter '*.png' | Sort-Object Name | ForEach-Object {
    & (Join-Path $PSScriptRoot 'ocr.ps1') $_.FullName (Join-Path $OutputDirectory ($_.BaseName + '.json'))
    $pageCount++
    if ($pageCount % 10 -eq 0) { Write-Output "OCR pages: $pageCount" }
}
