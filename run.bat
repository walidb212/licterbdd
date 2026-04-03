@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
py -3.10 -m prod_pipeline --brand both --steps all --continue-on-error %*
