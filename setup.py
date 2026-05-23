"""
Compiles Cython extensions with OpenMP and optimized C++ flags.

| Path: setup.py
| Project: amoginarium
| Created: 11.03.2026
| Authors: Nilusink, LukasKrah
"""

# ruff: disable[ERA001]
# from setuptools import setup
# from Cython.Build import cythonize
#
# setup(
#     name="_ccalculations",
#     ext_modules=cythonize("_ccalculations.pyx", compiler_directives={"boundscheck": False, "wraparound": False}),
#     zip_safe=False,
# )
# ruff: enable[ERA001]

import os
import sys

import setuptools.config.pyprojecttoml
from Cython.Build import cythonize
from setuptools import Extension, setup

setuptools.config.pyprojecttoml.read_configuration = lambda *_args, **_kwargs: {}


# 1. Determine OS-specific compiler flags for OpenMP and Maximum Speed
c_args = []
l_args = []

if sys.platform.startswith("win"):
    c_args = ["/O2", "/openmp", "/fp:fast"]
    l_args = ["/openmp"]

# 2. Dynamic File Discovery
extensions = []

base_package = "amoginarium"
cpp_files = [
    "_minrect.pyx",
    "_minrect_dirty.pyx",
    "_collision_manager.pyx",
    "_collision_methods.pyx",
]

for root, _, files in os.walk(base_package):
    for file in files:
        if file.endswith(".pyx"):
            path = os.path.join(root, file)
            module = path.replace(os.sep, ".")[:-4]  # remove .pyx

            # Determine if this specific file needs the C++ compiler
            lang = "c++" if file in cpp_files else "c"

            extensions.append(
                Extension(
                    name=module,
                    sources=[path],
                    language=lang,
                    extra_compile_args=c_args,
                    extra_link_args=l_args,
                )
            )

# 3. Build Setup
setup(
    ext_modules=cythonize(
        extensions,
        language_level="3",
        compiler_directives={
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
        },
    ),
)


# run with: python setup.py build_ext --inplace
