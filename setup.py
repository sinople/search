from distutils.core import setup
from setuptools import setup, find_packages

setup(name='search',
      version='0.1',
      description='Configurable Data Searching Tool',
      author='Sinople',
      packages=find_packages(exclude=['tests','tests.*']),
      include_package_data=True,
      )
