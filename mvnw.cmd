@echo off
setlocal

rem Maven Wrapper Script for Windows

set MAVEN_OPTS=-Xmx1024m -XX:MaxPermSize=256m
set MAVEN_HOME=%~dp0.mvn\wrapper
set MAVEN_CMD=%MAVEN_HOME%\mvn.cmd

if not exist "%MAVEN_CMD%" (
    echo Maven wrapper not found. Please run mvnw to download Maven.
    exit /b 1
)

"%MAVEN_CMD%" %* 

endlocal