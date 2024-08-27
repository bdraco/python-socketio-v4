"""
python-socketio-v4
---------------

Socket.IO server.
"""
import re
import sys
from setuptools import setup

with open('socketio_v4/__init__.py', 'r') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        f.read(), re.MULTILINE).group(1)

with open('README.rst', 'r') as f:
    long_description = f.read()

setup(
    name='python-socketio-v4',
    version=version,
    url='http://github.com/bdraco/python-socketio-v4/',
    license='MIT',
    author='Miguel Grinberg',
    author_email='miguelgrinberg50@gmail.com',
    description='Socket.IO server',
    long_description=long_description,
    packages=['socketio_v4'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'six>=1.9.0',
        'python-engineio-v3>=3.13.0,<4'
    ],
    extras_require={
        'client': [
            'requests>=2.21.0',
            'websocket-client>=0.54.0',
        ],
        'asyncio_client': [
            'aiohttp>=3.4',
            'websockets>=7.0',
        ]
    },
    tests_require=[
        'mock',
    ],
    test_suite='tests' if sys.version_info >= (3, 0) else 'tests.common',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
