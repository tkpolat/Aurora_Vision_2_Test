$Root   = (Get-Location).Path
$OutDir = Join-Path $Root '_dump'
$MaxKB  = 100

# atlanacak klasor adlari (herhangi bir seviyede)
$skipDirs  = @('.venv','venv','env','__pycache__','site-packages','.git','.vs',
               'bin','obj','node_modules','dist','build','.idea','TestResults','_dump')
# atlanacak dosyalar (yedek/patch copu)
$skipFiles = @('^app\.before','^app_yedek','^fix_','^diag_','^panel_test',
               'dump\.ps1$','topla\.ps1$','kontrol\.ps1$')
$exts      = @('.py','.json','.txt','.md')

$rootFull = (Resolve-Path $Root).Path
New-Item -ItemType Directory -Force $OutDir | Out-Null

$files = Get-ChildItem -Path $rootFull -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
    $rel   = $_.FullName.Substring($rootFull.Length).TrimStart('\')
    $parts = $rel -split '\\'
    $dirs  = $parts[0..([Math]::Max(0, $parts.Count - 2))]

    $skip = $false
    foreach ($d in $dirs) { if ($skipDirs -contains $d) { $skip = $true; break } }
    if ($skip) { return $false }

    foreach ($s in $skipFiles) { if ($rel -match $s) { return $false } }

    $exts -contains $_.Extension.ToLower()
} | Sort-Object FullName

if (-not $files) { Write-Host "DOSYA BULUNAMADI - dogru klasordeyim mi?" -ForegroundColor Red; exit }

# eski ciktilari temizle
Remove-Item (Join-Path $OutDir 'ONEMLI.md') -ErrorAction SilentlyContinue
Remove-Item (Join-Path $OutDir 'dump_part*.md') -ErrorAction SilentlyContinue

$files | ForEach-Object { $_.FullName.Substring($rootFull.Length).TrimStart('\') } |
    Set-Content (Join-Path $OutDir '00_tree.txt') -Encoding UTF8

$files | Select-Object @{n='rel';e={$_.FullName.Substring($rootFull.Length).TrimStart('\')}},
                       @{n='KB';e={[math]::Round($_.Length/1KB,1)}} |
    Sort-Object KB -Descending |
    Export-Csv (Join-Path $OutDir '00_manifest.csv') -NoTypeInformation -Encoding UTF8

$bt = [char]96; $f = "$bt$bt$bt"
$idx = 1; $buf = New-Object System.Text.StringBuilder; $bytes = 0
$enc = New-Object Text.UTF8Encoding($false)

foreach ($fl in $files) {
    $rel  = $fl.FullName.Substring($rootFull.Length).TrimStart('\')
    $lang = $fl.Extension.TrimStart('.').ToLower()
    $body = Get-Content -LiteralPath $fl.FullName -Raw -Encoding UTF8
    $block = "`n### FILE: $rel`n${f}${lang}`n$body`n${f}`n"
    $b = [Text.Encoding]::UTF8.GetByteCount($block)

    if ($bytes -gt 0 -and ($bytes + $b) -gt ($MaxKB * 1024)) {
        [IO.File]::WriteAllText((Join-Path $OutDir ("part{0:d2}.md" -f $idx)), $buf.ToString(), $enc)
        $idx++; [void]$buf.Clear(); $bytes = 0
    }
    [void]$buf.Append($block); $bytes += $b
}
if ($buf.Length -gt 0) {
    [IO.File]::WriteAllText((Join-Path $OutDir ("part{0:d2}.md" -f $idx)), $buf.ToString(), $enc)
}

Write-Host "$($files.Count) dosya -> $idx parca" -ForegroundColor Green
Get-ChildItem $OutDir -Filter 'part*.md' | ForEach-Object {
    Write-Host ("  {0}  ({1:N0} KB)" -f $_.Name, ($_.Length/1KB))
}
explorer $OutDir