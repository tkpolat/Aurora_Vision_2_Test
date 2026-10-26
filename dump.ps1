$Root   = (Get-Location).Path
$OutDir = Join-Path $Root '_dump'
$MaxKB  = 120

$excludeDirs = @('.git','bin','obj','.vs','node_modules','__pycache__','venv','.venv',
                 'env','dist','build','packages','.idea','TestResults','_dump')
$includeExt  = @('.py','.cs','.csproj','.sln','.json','.md','.txt','.xml','.yml','.yaml',
                 '.ini','.cfg','.toml','.bat','.ps1','.sh','.xaml','.cpp','.hpp','.h',
                 '.proto','.sql','.env')

$rootFull = (Resolve-Path $Root).Path
Write-Host "KAYNAK KLASOR : $rootFull"

$files = Get-ChildItem -Path $rootFull -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
    $rel  = $_.FullName.Substring($rootFull.Length).TrimStart('\')
    $dirs = ($rel -split '\\')[0..([Math]::Max(0,($rel -split '\\').Count-2))]
    $skip = $false
    foreach ($d in $dirs) { if ($excludeDirs -contains $d) { $skip = $true; break } }
    (-not $skip) -and ($includeExt -contains $_.Extension.ToLower())
} | Sort-Object FullName

if (-not $files -or $files.Count -eq 0) {
    Write-Host "HIC DOSYA BULUNAMADI. Bu klasor proje klasoru mu?" -ForegroundColor Red
    exit
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$files | ForEach-Object { $_.FullName.Substring($rootFull.Length).TrimStart('\') } |
    Set-Content (Join-Path $OutDir '00_tree.txt') -Encoding UTF8

$files | Select-Object @{n='rel';e={$_.FullName.Substring($rootFull.Length).TrimStart('\')}},
                       @{n='KB';e={[math]::Round($_.Length/1KB,1)}} |
    Sort-Object KB -Descending |
    Export-Csv (Join-Path $OutDir '00_manifest.csv') -NoTypeInformation -Encoding UTF8

$bt = [char]96; $fence = "$bt$bt$bt"
$idx = 1; $buf = New-Object System.Text.StringBuilder; $bytes = 0
$enc = New-Object Text.UTF8Encoding($false)

foreach ($f in $files) {
    $rel  = $f.FullName.Substring($rootFull.Length).TrimStart('\')
    $body = Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8
    $lang = $f.Extension.TrimStart('.').ToLower()
    $block = "`n### FILE: $rel`n${fence}${lang}`n$body`n${fence}`n"
    $b = [Text.Encoding]::UTF8.GetByteCount($block)
    if ($bytes -gt 0 -and ($bytes + $b) -gt ($MaxKB*1024)) {
        [IO.File]::WriteAllText((Join-Path $OutDir ("dump_part{0:d2}.md" -f $idx)), $buf.ToString(), $enc)
        $idx++; [void]$buf.Clear(); $bytes = 0
    }
    [void]$buf.Append($block); $bytes += $b
}
if ($buf.Length -gt 0) {
    [IO.File]::WriteAllText((Join-Path $OutDir ("dump_part{0:d2}.md" -f $idx)), $buf.ToString(), $enc)
}

Write-Host "$($files.Count) dosya, $idx parca uretildi." -ForegroundColor Green
Write-Host "Cikti: $OutDir" -ForegroundColor Green
explorer $OutDir