from setuptools import setup, find_packages

setup(
    name="pulse-cluster",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "scipy", 
        "matplotlib",
        "pandas",
        "pytest"
    ],
    python_requires=">=3.8",
    author="PulseDB Analysis Team",
    description="Time-Series Clustering and Segment Analysis on PulseDB Using Divide-and-Conquer Algorithms",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)
