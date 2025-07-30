@echo off
echo ===============================================
echo FOCUSED SysCacheLog986 SEARCH
echo ===============================================

echo [1] SEARCHING ALL LOCATIONS FOR SysCacheLog986
echo ===============================================
echo.
echo 🔍 Searching entire C: drive for SysCacheLog986 folders:
dir C:\ /s /ad /b 2>nul | findstr /i "SysCacheLog986"

echo.
echo [2] DETAILED ANALYSIS OF EACH LOCATION
echo ===============================================

for /f %%i in ('dir C:\ /s /ad /b 2^>nul ^| findstr /i "SysCacheLog986"') do (
    echo.
    echo ============================================
    echo 📁 ANALYZING: %%i
    echo ============================================
    
    echo File count in this location:
    dir "%%i" /s /a-d 2>nul | find /c ".txt" >nul && (
        for /f %%j in ('dir "%%i" /s /a-d /b 2^>nul ^| find /c /v ""') do echo   Total files: %%j
    ) || echo   Total files: 0
    
    echo.
    echo Checking for video cache folder:
    if exist "%%i\cache\vid" (
        echo   ✅ HAS cache\vid folder!
        echo   Video files in cache\vid:
        dir "%%i\cache\vid" /b 2>nul
        echo   Video file count:
        for /f %%k in ('dir "%%i\cache\vid" /a-d /b 2^>nul ^| find /c /v ""') do echo     %%k video files
    ) else (
        echo   ❌ No cache\vid folder
    )
    
    echo.
    echo Checking for backup video folder:
    if exist "%%i\backup\vid" (
        echo   ✅ HAS backup\vid folder!
        echo   Backup video files:
        dir "%%i\backup\vid" /b 2>nul
    ) else (
        echo   ❌ No backup\vid folder
    )
    
    echo.
    echo Folder creation date:
    dir "%%i" | findstr "%%~nxi"
    
    echo ============================================
)

echo.
echo [3] COMPARING CONFIG VS ACTUAL LOCATIONS
echo ===============================================
echo.
echo Config file points to:
echo   C:\Users\welcome\AppData\Local\Microsoft\Windows\INetCache\Content.IE5\SysCacheLog986
echo.
echo Checking if config location exists and has files:
if exist "C:\Users\welcome\AppData\Local\Microsoft\Windows\INetCache\Content.IE5\SysCacheLog986" (
    echo   ✅ Config location EXISTS
    for /f %%j in ('dir "C:\Users\welcome\AppData\Local\Microsoft\Windows\INetCache\Content.IE5\SysCacheLog986" /s /a-d /b 2^>nul ^| find /c /v ""') do echo   Files in config location: %%j
) else (
    echo   ❌ Config location DOES NOT EXIST
)

echo.
echo [4] REGISTRY CROSS-REFERENCE
echo ===============================================
echo Registry shows these video file paths:
reg query "HKEY_CURRENT_USER\Software\Classes\Local Settings\Software\Microsoft\Windows\CurrentVersion\AppModel\SystemAppData\Microsoft.ZuneMusic_8wekyb3d8bbwe\PersistedStorageItemTable\ManagedByApp" /s 2>nul | findstr "SysCacheLog986"

echo.
echo [5] QUICK FILE RECOVERY CHECK
echo ===============================================
echo Let's see if your video files are actually in any of these locations:

for /f %%i in ('dir C:\ /s /ad /b 2^>nul ^| findstr /i "SysCacheLog986"') do (
    if exist "%%i\cache\vid" (
        echo.
        echo 🎬 CHECKING FOR YOUR SPECIFIC VIDEO FILES in: %%i\cache\vid
        if exist "%%i\cache\vid\vault_20250708_114726_348552_test.mov" echo   ✅ FOUND: vault_20250708_114726_348552_test.mov
        if exist "%%i\cache\vid\vault_20250708_114722_640845_testing.mp4" echo   ✅ FOUND: vault_20250708_114722_640845_testing.mp4  
        if exist "%%i\cache\vid\VID-20250704-WA0002.mp4" echo   ✅ FOUND: VID-20250704-WA0002.mp4
        
        echo   All .mp4 and .mov files in this location:
        dir "%%i\cache\vid\*.mp4" /b 2>nul
        dir "%%i\cache\vid\*.mov" /b 2>nul
    )
)

echo.
echo ===============================================
echo FOCUSED SEARCH COMPLETE
echo ===============================================