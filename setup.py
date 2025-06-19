from setuptools import setup, find_packages
from os import path
from nepse_scraper import __version__

current_dir = path.abspath(path.dirname(__file__))

DESCRIPTION = 'Python Scraper for Nepse'

with open(path.join(current_dir, 'README.md'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

# Setting up
setup(
    name="nepse_scraper",
    version=__version__,
    author="Rabindra Basnet",
    author_email="rabindraabasnet@gmail.com",
    package_data={'nepse_scraper': ['*.wasm']},
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.6',
  ],
)
