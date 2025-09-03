from setuptools import setup,find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="MULTI_AI_AGENT",
    version = "0.1",
    author = "Sanjeev",
    packages=find_packages(),
    install_requires = requirements,
)