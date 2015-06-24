#!/usr/bin/env python

from distutils.core import setup

setup(name='TES Arena Exe Utils',
      version='1.0',
      description='TES Arena Exe Conversion Utilities',
      author='Oleksii Kuchma',
      author_email='nod3pad@gmail.com',
      url='https://github.com/Nodepad/python-tes-arena-exe-translator',
      packages=['TESAExe'],
      package_data={'TESAExe': ['exe.xml']}
     )
