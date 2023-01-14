@echo off
cls
echo [32mCHECKSTYLE INITIATED[0m

for /f %%x in ('dir /s/b *.py') do (
    python -m pycodestyle --first %%x
)

cmd /k