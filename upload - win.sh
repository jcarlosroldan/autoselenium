rm build -R
rm dist -R
rm autoselenium.egg-info -R
rm autoselenium-* -R
read -p "Please, open setup.py and update the version."
git add .
git commit
git push origin master
python setup.py sdist bdist_wheel
python -m twine upload dist/*
pip uninstall autoselenium
pip install autoselenium -U