from setuptools import setup, find_packages

setup(
    name='nse_data_fetcher',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'feedparser',
        'sqlalchemy',
        'requests',
    ],
    author='Clg-Rev_Sek',
    author_email='your.email@example.com',
    description='A package for fetching NSE data',
    url='https://github.com/yourusername/nse_data_fetcher',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
