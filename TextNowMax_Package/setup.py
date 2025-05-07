import setuptools

setuptools.setup(
    name="ProgressGhostCreator",
    version="1.0.0",
    author="PB BETTING",
    author_email="example@progressghostcreator.com",
    description="TextNow Ghost Account Creator with PB BETTING branding",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas",
        "pillow",
        "pyttsx3",
        "pydub",
    ],
)