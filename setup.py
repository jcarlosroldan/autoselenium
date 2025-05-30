from setuptools import find_packages, setup
from sys import version_info

assert version_info.major == 3 and version_info.minor >= 10, 'Python 3.10+ required'

with open('README.md', 'r', encoding='utf-8') as fp:
    long_description = fp.read()

with open('requirements.txt', 'r', encoding='utf-8') as fp:
    requirements = fp.read().strip().split()

setup(
    name='autoselenium',
    version='1.0.0',
    author='J. Carlos Roldán',
    author_email='juancarlos@sevilla.es',
    description='Ready-to-run Selenium.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=requirements,
    url='https://github.com/juancroldan/autoselenium',
    packages=find_packages(),
    package_data={'': ['resources/add_render.js']},
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
)
