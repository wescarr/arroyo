from typing import Sequence

from setuptools import find_packages, setup


def get_requirements() -> Sequence[str]:
    with open(u"requirements.txt") as fp:
        return [x.strip() for x in fp.read().split("\n") if not x.startswith("#")]


setup(
    name="arroyo",
    version="0.0.1",
    author="Sentry Team and Contributors",
    author_email="hello@sentry.io",
    license="Apache-2.0",
    url="https://github.com/getsentry/arroyo",
    packages=find_packages(exclude=["tests"]),
    package_data={"arroyo": ["py.typed"]},
    zip_safe=False,
    install_requires=get_requirements(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)