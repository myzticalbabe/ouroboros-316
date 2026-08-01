@echo off
start powershell -NoExit -ExecutionPolicy Bypass -Command "Write-Host 'Starting continuous 5-min recorder...' -ForegroundColor Cyan; & '%~dp0Record_Continuous.ps1'"
