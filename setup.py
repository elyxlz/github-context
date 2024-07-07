from setuptools import setup, find_packages

setup(
    name="github-context",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "PyGithub",
        "pyperclip",
        "tqdm",
    ],
    entry_points={
        "console_scripts": [
            "ghc=github_context.github_context:main",
        ],
    },
    author="Elio Pascarelli",
    author_email="elio@pascarelli.com",
    description="A CLI tool to quickly extract context from GitHub repositories for AI",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/elyxlz/github-context",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires='>=3.6',
)
