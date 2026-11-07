@echo off
chcp 65001 >nul
title CraftLang Фабрика Файлов
cls

set "WORK_DIR=%~dp0"

:MENU
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║         CraftLang Фабрика Файлов       ║
echo ╚════════════════════════════════════════╝
echo.
echo           [1] Создать исходный код (.cl)
echo           [2] Создать пустой файл (.txt, .md, .json...)
echo           [3] Собрать проект в .EXE
echo           [4] Собрать проект в .CMD
echo           [5] Запустить .CL скрипт
echo.
echo           [6] Мастер создания (EXE, ZIP, JS...) <-- НОВОЕ
echo.
echo           [0] Выход
echo.
set /p ACTION="Введи номер и нажми Enter: "

if "%ACTION%"=="1" goto CREATE_CL
if "%ACTION%"=="2" goto CREATE_EMPTY
if "%ACTION%"=="3" goto BUILD_EXE
if "%ACTION%"=="4" goto BUILD_CMD
if "%ACTION%"=="5" goto RUN_SCRIPT
if "%ACTION%"=="6" goto FILE_MASTER
if "%ACTION%"=="0" exit
goto MENU


:: --- МАСТЕР СОЗДАНИЯ РАЗНЫХ ФАЙЛОВ ---
:FILE_MASTER
cls
echo ╔════════════════════════════════════════╗
echo ║        Мастер создания файлов          ║
echo ╚════════════════════════════════════════╝
echo.
echo Что создать?
echo.
echo [1] Игра (.exe)          [2] Архив (.zip)
echo [3] Скрипт (.py)         [4] Страница (.html)
echo [5] Стили (.css)         [6] Код (.js)
echo [7] Данные (.json)       [8] Текст (.txt/.md)
echo [9] Код C# (.cs)         [10] Код C (.c/.h)
echo.
set /p TYPE="Введи номер типа файла: "

set "EXT="
set "DEFAULT_NAME="

if "%TYPE%"=="1" set "EXT=exe" & set "DEFAULT_NAME=Game"
if "%TYPE%"=="2" set "EXT=zip" & set "DEFAULT_NAME=Archive"
if "%TYPE%"=="3" set "EXT=py" & set "DEFAULT_NAME=script"
if "%TYPE%"=="4" set "EXT=html" & set "DEFAULT_NAME=index"
if "%TYPE%"=="5" set "EXT=css" & set "DEFAULT_NAME=style"
if "%TYPE%"=="6" set "EXT=js" & set "DEFAULT_NAME=app"
if "%TYPE%"=="7" set "EXT=json" & set "DEFAULT_NAME=data"
if "%TYPE%"=="8" set "EXT=txt" & set "DEFAULT_NAME=readme"
if "%TYPE%"=="9" set "EXT=cs" & set "DEFAULT_NAME=Program"
if "%TYPE%"=="10" set "EXT=c" & set "DEFAULT_NAME=main"

if "%EXT%"=="" (
    echo Неверный выбор.
    pause
    goto MENU
)

cls
set /p FILE_NAME="Введи имя файла (без .%EXT%): "
if "%FILE_NAME%"=="" set FILE_NAME=%DEFAULT_NAME%

:: --- ЛОГИКА СОЗДАНИЯ ---
if "%EXT%"=="exe" (
    goto BUILD_EXE_QUICK
)

if "%EXT%"=="zip" (
    goto CREATE_ZIP
)

:: Для всех остальных текстовых файлов
(
    if "%EXT%"=="html" echo ^<html^>^<body^>^<h1^>%FILE_NAME%^</h1^>^</body^>^</html^>
    if "%EXT%"=="css" echo body { background: #222; color: white; }
    if "%EXT%"=="js" echo console.log('JS File %FILE_NAME% loaded');
    if "%EXT%"=="json" echo { "project": "%FILE_NAME%", "version": "1.0" }
    if "%EXT%"=="py" echo print("Hello from %FILE_NAME%.py")
    if "%EXT%"=="cs" echo using System;^npublic class %FILE_NAME% {^n^n}
    if "%EXT%"=="c" echo #include ^<stdio.h^>^nint main() {^n^n    return 0;^n}
) > "%WORK_DIR%%FILE_NAME%.%EXT%"

cls
echo Файл "%FILE_NAME%.%EXT%" успешно создан в папке "%WORK_DIR%".
pause
goto MENU


:: --- Создание пустой игры .cl для дальнейшей сборки ---
:CREATE_CL
cls
set /p NAME="Введи имя файла (без .cl): "
if "%NAME%"=="" set NAME=my_project
(
echo игра
echo пусть ширина = 800
echo пусть высота = 600
echo окно = создать окно
echo запустить игру
) > "%WORK_DIR%%NAME%.cl"
cls
echo Файл "%NAME%.cl" создан.
pause
goto MENU

:: --- Создание абсолютно пустого файла ---
:CREATE_EMPTY
cls
set /p NAME="Введи имя файла (с расширением, например notes.txt): "
if "%NAME%"=="" goto MENU
type nul > "%WORK_DIR%%NAME%"
cls
echo Пустой файл "%NAME%" создан.
pause
goto MENU


:: --- Сборка в EXE (через пункт меню) ---
:BUILD_EXE
cls
set /p FILE="Введи имя файла .cl (без расширения): "
if "%FILE%"=="" goto MENU
if not exist "%WORK_DIR%%FILE%.cl" (
    echo Файл "%FILE%.cl" не найден.
    pause
    goto MENU
)
:BUILD_EXE_QUICK
cls
echo Сборка %FILE%.exe...
py "%WORK_DIR%craftlang.py" "%WORK_DIR%%FILE%.cl" --build
echo Сборка завершена. Файл в папке "dist".
pause
goto MENU


:: --- Создание ZIP архива ---
:CREATE_ZIP
cls
set /p FOLDER="Введи имя папки, которую заархивировать: "
if not exist "%WORK_DIR%%FOLDER%" (
    echo Папка "%FOLDER%" не найдена.
    pause
    goto MENU
)
cls
echo Создание архива %FILE_NAME%.zip...
powershell -Command "Compress-Archive -Path '%WORK_DIR%%FOLDER%\*' -DestinationPath '%WORK_DIR%%FILE_NAME%.zip'" -Force
cls
echo Архив "%FILE_NAME%.zip" создан.
pause
goto MENU


:BUILD_CMD
cls
set /p FILE="Введи имя файла (без .cl): "
if "%FILE%"=="" goto MENU
if not exist "%WORK_DIR%%FILE%.cl" (
    echo ОШИБКА: Файл "%FILE%.cl" не найден.
    pause
    goto MENU
)
cls
echo Идет сборка %FILE%.cmd...
set "SOURCE="
for /f "usebackq delims=" %%A in ("%WORK_DIR%%FILE%.cl") do call set "SOURCE=%%SOURCE%%%%A%%newline%%"
py -c "import sys; sys.path.append(r'%WORK_DIR%'); from craftlang import build_project; build_project(r'%WORK_DIR%%FILE%.cl', open(r'%WORK_DIR%%FILE%.cl', encoding='utf-8').read(), {})"
echo.
echo Сборка завершена. Файл лежит в папке "dist".
pause
goto MENU

:RUN_SCRIPT
cls
set /p FILE="Введи имя файла (без .cl): "
if "%FILE%"=="" goto MENU
if not exist "%WORK_DIR%%FILE%.cl" (
    echo ОШИБКА: Файл "%FILE%.cl" не найден.
    pause
    goto MENU
)
cls
echo Запуск %FILE%.cl...
py "%WORK_DIR%craftlang.py" "%WORK_DIR%%FILE%.cl"
pause
goto MENU