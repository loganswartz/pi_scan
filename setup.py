#!/usr/bin/env python3
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pi_scan",
    version="1.0.0",
    author="Logan Swartzendruber",
    author_email="logan.swartzendruber@gmail.com",
    description="Convert a Raspberry Pi (or Linux device) into a headless scanner station.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/loganswartz/pi_scan",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
