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

extensions = []

base_package = "amoginarium"

for root, _, files in os.walk("amoginarium"):
    for file in files:
        if file.endswith(".pyx"):
            path = os.path.join(root, file)

            module = path.replace(os.sep, ".")[:-4]  # remove .pyx
            extensions.append(Extension(module, [path]))

setup(
    ext_modules=cythonize(
        extensions,
        language_level=3,
        compiler_directives={
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True
        }
    )
)
