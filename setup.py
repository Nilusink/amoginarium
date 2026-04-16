# from setuptools import setup
# from Cython.Build import cythonize
#
# setup(
#     name="_ccalculations",
#     ext_modules=cythonize("_ccalculations.pyx", compiler_directives={"boundscheck": False, "wraparound": False}),
#     zip_safe=False,
# )
from setuptools import setup, Extension
from Cython.Build import cythonize
import os
import sys

# 1. Determine OS-specific compiler flags for OpenMP and Maximum Speed
c_args = []
l_args = []

if sys.platform.startswith("win"):
    # Windows (MSVC)
    c_args = ['/O2', '/openmp', '/fp:fast']
    l_args = ['/openmp']
elif sys.platform.startswith("linux"):
    # Linux (GCC/Clang)
    c_args = ['-O3', '-fopenmp', '-ffast-math', '-march=native']
    l_args = ['-fopenmp']
elif sys.platform.startswith("darwin"):
    # macOS (Requires `brew install libomp` in terminal first)
    c_args = ['-O3', '-Xpreprocessor', '-fopenmp']
    l_args = ['-lomp']

# 2. Dynamic File Discovery
extensions = []

base_package = "amoginarium"
cpp_files = ["_minrect.pyx", "_minrect_dirty.pyx", "_aabb_aabb_cython.pyx"]

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
            "cdivision": True
        }
    )
)


# run with: python setup.py build_ext --inplace
