"""
my_tools/setup.py

Project: amoginarium
Created: 28.04.2026
Authors: LukasKrah
"""

from setuptools import setup


setup(
    name='amoginarium-tools',
    version='1.0',
    packages=['arch_gen'],
    entry_points={
        'console_scripts': [
            'update_readme=arch_gen.generate_architecture:main',
        ],
    },
)

# pip install -e .
