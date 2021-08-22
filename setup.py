from setuptools import (
    find_packages,
    setup,
)

setup(
    version="0.1.0",
    name="omnik",
    packages=find_packages(),
    install_requires=["influxdb"],
    entry_points={
        "console_scripts": [
            "omnik = omnik.main:main",
        ],
    },
)
