# Renderiza todos los diagramas PlantUML de docs/diagrams a PNG y SVG usando Docker.
# Uso:  .\scripts\render-diagrams.ps1
$root = Split-Path -Parent $PSScriptRoot
$diagrams = Join-Path $root "docs\diagrams"
docker run --rm -v "${diagrams}:/data" plantuml/plantuml -tpng "/data/*.puml"
docker run --rm -v "${diagrams}:/data" plantuml/plantuml -tsvg "/data/*.puml"
Get-ChildItem $diagrams -Include *.png, *.svg -Recurse | Select-Object Name, Length
