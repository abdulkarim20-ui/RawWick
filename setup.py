from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rawwick",
    version="0.1.0",
    author="AbdulKarim",
    author_email="abdulkarimsalimshaikh@gmail.com",
    description="A robust and scalable AI voice assistant demonstrating best practices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/abdulkarim20-ui/RawWick",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "speech_recognition>=3.8.1",
        "rich>=12.0.0",
        "requests>=2.28.0",
        "psutil>=5.9.0",
    ],
)