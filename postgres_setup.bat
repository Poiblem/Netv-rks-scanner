@echo off
setlocal EnableDelayedExpansion

:: ============================================================
:: Variabler - kan aendres
:: ============================================================
set DB_USER=server_admin
set DB_PASSWORD=123
set DB_NAME=server_cve

:: PostgreSQL installer indstillinger
set PG_VERSION=16
set PG_INSTALL_DIR=C:\Program Files\PostgreSQL\%PG_VERSION%
set PG_DATA_DIR=%PG_INSTALL_DIR%\data
set PG_BIN=%PG_INSTALL_DIR%\bin
set PG_HBA=%PG_DATA_DIR%\pg_hba.conf
set PG_INSTALLER=postgresql_installer.exe

:: Download URL til PostgreSQL 16 Windows installer (EnterpriseDB)
set PG_DOWNLOAD_URL=https://get.enterprisedb.com/postgresql/postgresql-16.8-1-windows-x64.exe

:: Track hvilke steps vi har gennemfoert, til brug for rollback
set POSTGRES_DOWNLOADED=false
set POSTGRES_INSTALLED=false
set DB_CREATED=false
set PG_HBA_MODIFIED=false

:: ============================================================
:: Cleanup / rollback funktion
:: Kaldes ved fejl via GOTO cleanup_on_error
:: ============================================================
goto :main

:cleanup_on_error
    echo.
    echo Fejl opstod - oprydning starter...

    if "!DB_CREATED!"=="true" (
        echo  Sletter database og bruger...
        "!PG_BIN!\psql.exe" -U postgres -c "DROP DATABASE IF EXISTS !DB_NAME!;" 2>nul
        "!PG_BIN!\psql.exe" -U postgres -c "DROP USER IF EXISTS !DB_USER!;" 2>nul
    )

    if "!PG_HBA_MODIFIED!"=="true" (
        if exist "!PG_HBA!.backup" (
            echo  Gendanner pg_hba.conf fra backup...
            copy /Y "!PG_HBA!.backup" "!PG_HBA!" >nul
            del "!PG_HBA!.backup" 2>nul
        )
    )

    if "!POSTGRES_INSTALLED!"=="true" (
        echo  Stopper og afinstallerer PostgreSQL...
        net stop postgresql-x64-%PG_VERSION% 2>nul
        sc delete postgresql-x64-%PG_VERSION% 2>nul
        :: Koer uninstalleren hvis den findes
        if exist "!PG_INSTALL_DIR!\uninstall-postgresql.exe" (
            "!PG_INSTALL_DIR!\uninstall-postgresql.exe" --mode unattended 2>nul
        )
    )

    if "!POSTGRES_DOWNLOADED!"=="true" (
        if exist "!PG_INSTALLER!" (
            echo  Sletter installer fil...
            del "!PG_INSTALLER!" 2>nul
        )
    )

    echo.
    echo Rollback komplet. Script afslutter uden installation.
    exit /b 1

:: ============================================================
:: Hjaelpefunktion - tjek om en kommando lykkedes
:: Brug: call :check_error "Beskrivelse af fejl"
:: ============================================================
:check_error
    if !ERRORLEVEL! NEQ 0 (
        echo FEJL: %~1
        goto cleanup_on_error
    )
    goto :eof

:: ============================================================
:: MAIN
:: ============================================================
:main

echo ============================================================
echo  PostgreSQL Database Setup - Windows
echo ============================================================
echo.

:: Tjek om scriptet korer som administrator
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo FEJL: Scriptet skal kores som Administrator.
    echo Hoejreklik paa filen og vaelg "Koer som administrator".
    pause
    exit /b 1
)

:: Tjek om psql allerede er installeret
if exist "%PG_BIN%\psql.exe" (
    echo PostgreSQL ser ud til allerede at vaere installeret i:
    echo  %PG_INSTALL_DIR%
    echo.
    set /p REINSTALL="Vil du fortsaette og kun oprette database/bruger? (j/n): "
    if /i "!REINSTALL!"=="j" goto :skip_install
    echo Afslutter.
    exit /b 0
)

:: ============================================================
:: 1. step - Download PostgreSQL installer
:: ============================================================
echo [1/7] Downloader PostgreSQL %PG_VERSION% installer...
echo  URL: %PG_DOWNLOAD_URL%
echo  Dette kan tage et stykke tid...
echo.

:: Brug PowerShell til at downloade (tilgaengelig pa Windows 7+)
powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('%PG_DOWNLOAD_URL%', '%PG_INSTALLER%') }"
call :check_error "Download af PostgreSQL installer fejlede"
set POSTGRES_DOWNLOADED=true
echo  Download faerdig.
echo.

:: ============================================================
:: 2. step - Installer PostgreSQL silent (uden GUI)
:: ============================================================
echo [2/7] Installerer PostgreSQL (stille installation)...
echo  Installationsmappe: %PG_INSTALL_DIR%
echo  Dette kan tage et par minutter...
echo.

:: --mode unattended = ingen GUI
:: --superpassword = sat postgres superbruger password til "postgres" (kan aendres)
:: --servicename = Windows service navn
:: --serviceaccount og --servicepassword = Windows service bruger
"%PG_INSTALLER%" ^
    --mode unattended ^
    --unattendedmodeui none ^
    --superpassword postgres ^
    --servicename "postgresql-x64-%PG_VERSION%" ^
    --serviceaccount "NT AUTHORITY\NetworkService" ^
    --prefix "%PG_INSTALL_DIR%" ^
    --datadir "%PG_DATA_DIR%" ^
    --enable-components server,commandlinetools ^
    --disable-components pgAdmin,stackbuilder

call :check_error "Installation af PostgreSQL fejlede"
set POSTGRES_INSTALLED=true

:: Slet installer efterfølgende
del "%PG_INSTALLER%" 2>nul
set POSTGRES_DOWNLOADED=false
echo  Installation faerdig.
echo.

:skip_install

:: Tilfoej PostgreSQL bin til PATH i denne session
set PATH=%PG_BIN%;%PATH%

:: ============================================================
:: 3. step - Start PostgreSQL service
:: ============================================================
echo [3/7] Starter PostgreSQL service...

net start postgresql-x64-%PG_VERSION% 2>nul
:: Vent et sekund saa PostgreSQL er klar
timeout /t 3 /nobreak >nul

:: Tjek at servicen korer
sc query postgresql-x64-%PG_VERSION% | find "RUNNING" >nul
call :check_error "PostgreSQL service startede ikke korrekt"
echo  PostgreSQL korer.
echo.

:: ============================================================
:: 4. step - Opret database bruger og database
:: ============================================================
echo [4/7] Opretter bruger '%DB_USER%' og database '%DB_NAME%'...

:: Brug postgres superbrugeren til at oprette vores bruger og database
:: PGPASSWORD sættes som miljovariabel saa psql ikke beder om password
set PGPASSWORD=postgres

"%PG_BIN%\psql.exe" -U postgres -h 127.0.0.1 -p 5432 -c "CREATE USER %DB_USER% WITH PASSWORD '%DB_PASSWORD%';"
call :check_error "Kunne ikke oprette database bruger"

"%PG_BIN%\psql.exe" -U postgres -h 127.0.0.1 -p 5432 -c "CREATE DATABASE %DB_NAME% OWNER %DB_USER%;"
call :check_error "Kunne ikke oprette database"

"%PG_BIN%\psql.exe" -U postgres -h 127.0.0.1 -p 5432 -c "GRANT ALL PRIVILEGES ON DATABASE %DB_NAME% TO %DB_USER%;"
call :check_error "Kunne ikke give rettigheder til bruger"

set DB_CREATED=true
echo  Bruger og database oprettet.
echo.

:: ============================================================
:: 5. step - Konfigurer pg_hba.conf (password authentication)
:: ============================================================
echo [5/7] Konfigurerer pg_hba.conf...

:: Backup den originale fil
copy /Y "%PG_HBA%" "%PG_HBA%.backup" >nul
call :check_error "Kunne ikke lave backup af pg_hba.conf"
set PG_HBA_MODIFIED=true

:: Pa Windows bruger vi PowerShell til at indsaette linjer i filen,
:: da Windows' batch ikke har en sed-akvivalent.
:: Vi tilfojer md5-regler for vores specifikke database og bruger
:: OBS: Pa Windows bruger PostgreSQL som standard "scram-sha-256".
:: Vi bruger "md5" her for at matche den originale Linux-opsaetning.

:: Indsaet IPv4 regel
powershell -Command ^
    "$content = Get-Content '%PG_HBA%'; " ^
    "$newLine = 'host    %DB_NAME%    %DB_USER%    127.0.0.1/32    md5'; " ^
    "$idx = ($content | Select-String -Pattern '^host\s+all\s+all\s+127\.0\.0\.1/32').LineNumber - 1; " ^
    "if ($idx -ge 0) { $content = $content[0..($idx-1)] + $newLine + $content[$idx..($content.Length-1)] } else { $content += $newLine }; " ^
    "Set-Content '%PG_HBA%' $content"
call :check_error "Kunne ikke opdatere pg_hba.conf med IPv4 regel"

:: Indsaet IPv6 regel
powershell -Command ^
    "$content = Get-Content '%PG_HBA%'; " ^
    "$newLine = 'host    %DB_NAME%    %DB_USER%    ::1/128         md5'; " ^
    "$idx = ($content | Select-String -Pattern '^host\s+all\s+all\s+::1/128').LineNumber - 1; " ^
    "if ($idx -ge 0) { $content = $content[0..($idx-1)] + $newLine + $content[$idx..($content.Length-1)] } else { $content += $newLine }; " ^
    "Set-Content '%PG_HBA%' $content"
call :check_error "Kunne ikke opdatere pg_hba.conf med IPv6 regel"

echo  pg_hba.conf opdateret.
echo.

:: ============================================================
:: 6. step - Genstart PostgreSQL for at loade ny konfiguration
:: ============================================================
echo [6/7] Genstarter PostgreSQL...

net stop postgresql-x64-%PG_VERSION% >nul
timeout /t 2 /nobreak >nul
net start postgresql-x64-%PG_VERSION% >nul
timeout /t 3 /nobreak >nul

sc query postgresql-x64-%PG_VERSION% | find "RUNNING" >nul
call :check_error "PostgreSQL kunne ikke genstarte"
echo  PostgreSQL genstartet.
echo.

:: ============================================================
:: 7. step - Test forbindelsen
:: ============================================================
echo [7/7] Tester forbindelse til databasen...

set PGPASSWORD=%DB_PASSWORD%
"%PG_BIN%\psql.exe" -U %DB_USER% -d %DB_NAME% -h 127.0.0.1 -p 5432 -c "SELECT version();" >nul 2>&1
"%PG_BIN%\psql.exe" -U %DB_USER% -d %DB_NAME% -h 127.0.0.1 -f "%~dp0database_layout.sql"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo  Faerdig! PostgreSQL database er klar til brug.
    echo.
    echo  Database:  %DB_NAME%
    echo  Bruger:    %DB_USER%
    echo  Password:  %DB_PASSWORD%
    echo  Host:      127.0.0.1:5432
    echo.
    echo  Backup af pg_hba.conf er gemt som:
    echo  %PG_HBA%.backup
    echo ============================================================
) else (
    echo FEJL: Kunne ikke forbinde til databasen.
    echo Tjek logs i Windows Eventlog eller:
    echo  %PG_DATA_DIR%\log\
    goto cleanup_on_error
)

endlocal
pause