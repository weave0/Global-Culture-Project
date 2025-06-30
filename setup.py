from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="culture-segmenter",
    version="0.1.0",
    description="Segment, enrich, and validate global culture profiles with AI and rules.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Brett Weaver",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pandas",
        "openai",
        "tiktoken",
        "python-docx",
        "streamlit",
        "pytest",
    ],
    entry_points={
        "console_scripts": [
            "culture-segmenter=scripts.segment_by_culture:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Education",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.9",
)
