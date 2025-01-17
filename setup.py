from setuptools import setup, find_packages

setup(
    name="async-substrate-interface",
    version="1.0.0rc3",
    description="Asyncio library for interacting with substrate.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Opentensor Foundation",
    author_email="benhimes@opentensor.dev",
    url="https://github.com/opentensor/async-substrate-interface",
    packages=find_packages(),
    install_requires=[
        "asyncstdlib~=3.13.0",
        "bittensor-wallet>=2.1.3",
        "bt-decode==0.4.0",
        "scalecodec==1.2.11",
        "websockets>=14.1",
        "xxhash",
    ],
    python_requires=">=3.9,<3.13",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
