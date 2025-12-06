# Script de génération de l'exécutable pour Windows (facturation_ci)
# Ce script doit être lancé depuis la racine du projet via PowerShell.

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Génération de l'exécutable FacturationCI" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Vérification de l'installation de PyInstaller
if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "[INFO] PyInstaller n'est pas trouvé. Tentative d'installation..." -ForegroundColor Yellow
    try {
        pip install pyinstaller
    } catch {
        Write-Host "[ERREUR] Impossible d'installer PyInstaller. Vérifiez votre installation Python." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[OK] PyInstaller est installé." -ForegroundColor Green
}

# 2. Nettoyage des dossiers de build précédents
Write-Host "[INFO] Nettoyage des anciens fichiers de build..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "*.spec") { Remove-Item -Force "*.spec" }

# 3. Configuration des chemins
$EntryPoint = "facturation_ci/main.py"
$TemplatesSrc = "facturation_ci/templates"
$ImagesSrc = "facturation_ci/images"

# Recherche de l'icône (User request vs Repo structure)
$IconPathCandidate1 = "facturation_ci/images/icon.ico"
$IconPathCandidate2 = "images/icon.ico"
$IconPath = ""

if (Test-Path $IconPathCandidate1) {
    $IconPath = $IconPathCandidate1
} elseif (Test-Path $IconPathCandidate2) {
    $IconPath = $IconPathCandidate2
}

if (-not (Test-Path $EntryPoint)) {
    Write-Host "[ERREUR] Le fichier d'entrée $EntryPoint est introuvable." -ForegroundColor Red
    exit 1
}

if ($IconPath -eq "") {
    Write-Host "[ATTENTION] L'icône (icon.ico) est introuvable dans facturation_ci/images ou images/." -ForegroundColor Yellow
    Write-Host "L'icône par défaut sera utilisée." -ForegroundColor Yellow
}

# 4. Construction de la commande PyInstaller
# Notes :
# --noconfirm : Écrase sans demander
# --onedir : Dossier unique (plus fiable pour les assets que onefile)
# --windowed : Pas de console noire
# --clean : Cache propre
# --add-data : "Source;Destination" (Séparateur Windows ;)
# --collect-all playwright : Tente de récupérer les dépendances Playwright (browsers non inclus)

Write-Host "[INFO] Lancement de PyInstaller..." -ForegroundColor Cyan

# Construction de la liste des arguments
$PyInstallerArgs = @(
    "--noconfirm",
    "--onedir",
    "--windowed",
    "--clean",
    "--name", "FacturationCI",
    "--add-data", "$TemplatesSrc;templates",
    "--add-data", "$ImagesSrc;images",
    "--hidden-import", "mysql.connector",
    "--hidden-import", "babel.numbers",
    "--collect-all", "playwright"
)

# Ajout conditionnel de l'icône
if ($IconPath -ne "") {
    $PyInstallerArgs += "--icon"
    $PyInstallerArgs += $IconPath
}

# Ajout du fichier d'entrée à la fin
$PyInstallerArgs += "$EntryPoint"

# Affichage de la commande pour débogage
Write-Host "Arguments: $PyInstallerArgs" -ForegroundColor Gray

# Exécution
# Note: Dans PowerShell, appeler un exécutable avec un tableau d'arguments sépare correctement chaque élément.
& pyinstaller $PyInstallerArgs

# 5. Vérification du résultat
if ($?) {
    Write-Host "`n==================================================" -ForegroundColor Green
    Write-Host "   SUCCÈS ! L'exécutable a été généré." -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host "Emplacement : dist/FacturationCI/FacturationCI.exe" -ForegroundColor White
    Write-Host "Note : Pour le bon fonctionnement de la génération PDF," -ForegroundColor Gray
    Write-Host "assurez-vous que les navigateurs Playwright sont installés sur la machine cible." -ForegroundColor Gray
} else {
    Write-Host "`n==================================================" -ForegroundColor Red
    Write-Host "   ÉCHEC de la génération." -ForegroundColor Red
    Write-Host "==================================================" -ForegroundColor Red
}
