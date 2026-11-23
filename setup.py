from setuptools import setup, find_packages
setup(
    name="ouroboros-316",
    version="0.1.0",
    packages=find_packages(),
    entry_points={"console_scripts": ["ouroboros=ouroboros.cli:main"]},
)