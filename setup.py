# -*- coding: utf-8 -*-

from os import path
import setuptools

readme_file = path.join(path.dirname(path.abspath(__file__)), 'README.md')
try:
    from m2r import parse_from_file
    readme = parse_from_file(readme_file)
except ImportError:
    with open(readme_file) as f:
        readme = f.read()

install_requires=[]

setuptools.setup(
    name="dargs",
    setup_requires=['setuptools_scm'],
    use_scm_version={'write_to': 'dargs/_version.py'},
    author="Yixiao Chen",
    author_email="yixiaoc@princeton.edu",
    description="Process arguments for the deep modeling project.",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/deepmodeling/dargs",
    packages=['dargs'],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    ],
    install_requires=install_requires,
)

