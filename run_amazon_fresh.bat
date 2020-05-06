@echo off

cd %~dp0
%PYTHON3_SCRIPTS%\pipenv run python amazon_fresh.py
