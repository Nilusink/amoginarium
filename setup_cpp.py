from setuptools import setup, Extension
import pybind11
import sys

c_args = []
l_args = []

# Apply aggressive C++ compiler optimizations
if sys.platform.startswith("win"):
    c_args = ['/O2', '/openmp', '/fp:fast']
    l_args = ['/openmp']
elif sys.platform.startswith("linux"):
    c_args = ['-O3', '-fopenmp', '-ffast-math', '-march=native']
    l_args = ['-fopenmp']
elif sys.platform.startswith("darwin"):
    c_args = ['-O3', '-Xpreprocessor', '-fopenmp']
    l_args = ['-lomp']

ext_modules = [
    Extension(
        "cpp_engine",
        ["test/cpp_engine.cpp"],
        include_dirs=[pybind11.get_include()],
        language='c++',
        extra_compile_args=c_args,
        extra_link_args=l_args,
    )
]

setup(ext_modules=ext_modules)