#!/usr/bin/env python
import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def run_setup():
    setup(
        name='pydnode',
        version='0.0.1',
        description='',
        keywords = '',
        url='http://github.com/ybrs/pydnode',
        author='Aybars Badur',
        author_email='aybars.badur@gmail.com',
        license='BSD',
        packages=['pydnode'],
        install_requires=[
            'tornado>=3.1.1'
        ],
        test_suite='tests',
        long_description=read('README.md'),
        zip_safe=True,
        classifiers=[
        ]
    )

if __name__ == '__main__':
    run_setup()