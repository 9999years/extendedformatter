from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='uni2esky',
    version='0.0.1',

    description='''F-string literals for non-literal strings.''',
    # rst is some bull shit and i will not be party to it. markdown or die
    long_description='https://github.com/9999years/extendedformatter/blob/master/readme.md',
    url='https://github.com/9999years/extendedformatter',
    author='Rebecca Turner',
    author_email='637275@gmail.com',
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
        'Intended Audience :: Developers',
        # best thing for what's kind of a language extension?
        'Topic :: Software Development :: Pre-processors',
        'Natural Language :: English',
    ],

    keywords='f-string format templating',

    packages=find_packages(exclude=['contrib', 'docs', 'tests',]),

    # entry_points={
        # 'console_scripts': [
            # 'name = module:func',
        # ],
    # },
)
