from setuptools import setup

setup(
    name="TidalTime",
    version="1.0",
    packages=["tidal", "tidal.utils"],
    package_dir={"": "src"},
    install_requires=[
        "click>=8.1.3",
        "bs4>=0.0.1",
        "beautifulsoup4>=4.11.1",
        "requests>=2.28.2",
        "tenacity>=8.0.1",
        "pyserde>=0.12.2",
        "typing-extensions >= 4.8.0",
    ],
    url="",
    license="",
    author="Wei Liu",
    author_email="newway.lw@gmail.com",
    description="scrap UK tidal records from BBC.co.uk",
)
