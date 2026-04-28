from setuptools import setup

setup(
    name='amoginarium-tools',
    version='1.0',
    packages=['arch_gen'],
    entry_points={
        'console_scripts': [
            'gen_readme=arch_gen.generate_architecture:cmd_gen_readme',
            'update_readmes=arch_gen.generate_architecture:cmd_update_readmes',
            'create_readmes=arch_gen.generate_architecture:cmd_create_readmes',
        ],
    },
)

# pip install -e .
