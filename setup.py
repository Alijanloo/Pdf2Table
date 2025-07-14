from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="pdf2table",
    version="0.1.0",
    author="Pdf2Table Team",
    author_email="mahmoodjanlooali@gmail.com",
    description="A RAG application for indexing and inferring tables from PDF documents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Alijanloo/Pdf2Table",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
)