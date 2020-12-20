from setuptools import setup
from Cython.Build import cythonize

setup(
    name='SpaceX Assignment',
    ext_modules=cythonize("main.py"),
    zip_safe=False,
)