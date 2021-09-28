from distutils.core import setup
setup(
    name='valveexe',
    packages=['valveexe'],
    version='0.1.1',
    license='gpl-3.0',
    description='A library to interact with Source engine game\'s developer console',
    author='Maxime Dupuis',
    author_email='mdupuis@hotmail.ca',
    url='https://github.com/pySourceSDK/ValveEXE',
    download_url='https://github.com/pySourceSDK/ValveEXE/archive/v0.1.0.tar.gz',
    keywords=['exe', 'source', 'sourcesdk',
              'hammer', 'valve', 'game', 'client'],
    install_requires=['psutil', 'rcon'],
    classifiers=[
        'Development Status :: 3 - Alpha ',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.8',
    ],
)
