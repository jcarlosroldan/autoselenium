@ECHO OFF

Rem Remove auxiliary files
rd /s /q build 
rd /s /q dist
rd /s /q autoselenium.egg-info
for /d %%x in (autoselenium-*) do rd /s /q %%x

Rem Commit changes
git add *
git commit
git push origin master

Rem Update library
python setup.py sdist bdist_wheel
python -m twine upload dist/* -u juancroldan

Rem Remove auxiliary files again
rd /s /q build 
rd /s /q dist
rd /s /q autoselenium.egg-info
for /d %%x in (autoselenium-*) do rd /s /q %%x

timeout /t 5

Rem Reinstall it
ipconfig /flushdns
pip uninstall autoselenium -y
pip install autoselenium -U

pause