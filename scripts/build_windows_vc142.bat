:: #############################################################################
:: Example command to build on Windows for Visual Studio 2019 (VC142).
:: #############################################################################

@echo off
setlocal

SET ORIGINAL_DIR=%cd%
SET REPO_ROOT=%~dp0%..
SET DRAGON_ROOT=%REPO_ROOT%\dragon
SET THIRD_PARTY_DIR=%REPO_ROOT%\third_party
SET CMAKE_GENERATOR="Visual Studio 16 2019"

:: Build options
SET BUILD_PYTHON=ON
SET BUILD_RUNTIME=OFF

:: Protobuf SDK options
SET PROTOBUF_SDK_ROOT_DIR=%THIRD_PARTY_DIR%\protobuf

:: Protobuf Compiler options
:: Set the protobuf compiler(i.e., protoc) if necessary
:: If not, a compiler in the sdk or environment will be used
SET PROTOBUF_PROTOC_EXECUTABLE=%PROTOBUF_SDK_ROOT_DIR%\bin\protoc

:: Python options
:: Set your python "interpreter" if necessary
:: If not, a default interpreter will be used
:: SET PYTHON_EXECUTABLE=X:/Anaconda3/python
if %BUILD_PYTHON% == ON (
  if NOT DEFINED PYTHON_EXECUTABLE (
    for /F %%i in ('python -c "import sys;print(sys.executable)"') do (set PYTHON_EXECUTABLE=%%i)
  )
)

echo=
echo -------------------------  BUILDING CONFIGS -------------------------
echo=

echo -- DRAGON_ROOT=%DRAGON_ROOT%
echo -- CMAKE_GENERATOR=%CMAKE_GENERATOR%

if not exist %DRAGON_ROOT%\build mkdir %DRAGON_ROOT%\build
cd %DRAGON_ROOT%\build

cmake .. ^
  -G%CMAKE_GENERATOR% ^
  -Ax64 ^
  -DBUILD_PYTHON=%BUILD_PYTHON% ^
  -DBUILD_RUNTIME=%BUILD_RUNTIME% ^
  -DTHIRD_PARTY_DIR=%THIRD_PARTY_DIR% ^
  -DPROTOBUF_SDK_ROOT_DIR=%PROTOBUF_SDK_ROOT_DIR% ^
  -DPROTOBUF_PROTOC_EXECUTABLE=%PROTOBUF_PROTOC_EXECUTABLE% ^
  -DPYTHON_EXECUTABLE=%PYTHON_EXECUTABLE% ^
  || goto :label_error

echo=
echo -------------------------  BUILDING CONFIGS -------------------------
echo=

cmake --build . --target INSTALL --config Release -- /maxcpucount:%NUMBER_OF_PROCESSORS% || goto :label_error
cd %DRAGON_ROOT%
%PYTHON_EXECUTABLE% setup.py install || goto :label_error

echo=
echo Built successfully
cd %ORIGINAL_DIR%
endlocal
pause
exit /b 0

:label_error
echo=
echo Building failed
cd %ORIGINAL_DIR%
endlocal
pause
exit /b 1