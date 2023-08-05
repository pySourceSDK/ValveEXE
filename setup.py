from setuptools import setup, find_packages
import re

with open('README.md') as f:
    re_omit = r'<!--- start pypi omit -->.*<!--- end pypi omit -->'
    long_description = re.sub(re_omit, '', f.read(), flags=re.S)

VERSION = '{{VERSION_PLACEHOLDER}}'
if 'VERSION_PLACEHOLDER' in VERSION:
    VERSION = '0.0.0'

setup(
    name='valveexe',
    packages=['valveexe'],
    version=VERSION,
    description='A library to issue console commands to Source Engine game clients',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='gpl-3.0',
    author='Maxime Dupuis',
    author_email='mdupuis@hotmail.ca',
    url='https://pysourcesdk.github.io/ValveEXE/',
    project_urls={
        'Documentation': 'https://pysourcesdk.github.io/ValveEXE/',
        'Github': 'https://github.com/pySourceSDK/ValveEXE',
    },
    keywords=['exe', 'source', 'sourcesdk',
              'hammer', 'valve', 'game', 'client'],
    install_requires=['psutil', 'rcon'],
    classifiers=[
        'Development Status :: 3 - Alpha ',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Operating System :: Unix',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows'
    ],
)
