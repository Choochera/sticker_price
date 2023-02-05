@echo off
cd ../
cls
echo [32mCHECKSTYLE INITIATED[0m

for /f %%x in ('dir /s/b *.py') do (
    python -m pycodestyle --first %%x
)
cd Scripts
cmd /k