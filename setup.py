from setuptools import find_packages, setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='dialign_python',
    packages=find_packages(),
    install_requires = requirements,
    version='0.1.0',
    description='Python implementation of Dialign',
    author='anonymous',
)
