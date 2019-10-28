rm build -R
rm dist -R
rm autoselenium.egg-info -R
rm autoselenium-* -R
read -p "Please, open setup.py and update the version."
git add .
git commit
git push origin master
python3 setup.py sdist bdist_wheel
python3 -m twine upload dist/*
pip3 uninstall autoselenium
pip3 install autoselenium -U