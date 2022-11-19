# -*- coding: utf-8 -*-

from pathlib import Path

from setuptools import setup

__version__ = "1.0.0"

here = Path(__file__).parent
long_description = (here.parent / "README.md").read_text()
requirements = (here / "requirements.txt").read_text()

setup(
    name="mycampus_mobile",
    python_requires=">3.10.0",
    version=__version__,
    description=(
        "Mobile application submitted as software engineering project "
        "at the International University (IU), "
        "aiming for the academic degree in Computer Science (M.Sc.)."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Dawid Ciepiela",
    author_email="dawid.ciepiela@iu-study.org",
    package_dir={"mycampus_mobile": "."},
    packages=["mycampus_mobile", "mycampus_mobile.backend", "mycampus_mobile.frontend"],
    package_data={
        "mycampus_mobile": ["data/img/*", "data/logo/*"],
        "mycampus_mobile.frontend": ["kivy/*.kv"],
    },
    include_package_data=True,
    install_requires=requirements.splitlines(),
)
