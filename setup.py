"""Setup script for sonic-buildimage wheel compatibility.

This mirrors pyproject.toml for the sonic-buildimage build system
which expects setup.py for Python wheel builds inside Docker containers.
"""

from setuptools import setup

setup(
    name="sonic-troubleshooting-demo-service",
    version="0.1.0",
    description="SONiC troubleshooting demo service for port inspection and controlled remediation",
    author="Ronnit Burman",
    author_email="ronnitburman@gmail.com",
    packages=[
        "sonic_troubleshooting_demo_service",
    ],
    install_requires=[
        "redis>=5.0.0",
        "typer>=0.9.0",
        "rich>=13.7.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "sonic-troubleshooting-demo-service = sonic_troubleshooting_demo_service.main:main",
        ],
    },
    classifiers=[
        "Intended Audience :: System Administrators",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python",
    ],
    python_requires=">=3.9",
)
