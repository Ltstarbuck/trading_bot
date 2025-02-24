from setuptools import setup, find_packages

setup(
    name="trading_bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'pandas>=2.0.0',
        'numpy>=1.24.0',
        'ccxt>=4.0.0',
        'plotly>=5.18.0',
        'PyQt5>=5.15.0',
        'playsound>=1.3.0',
        'pydantic>=2.0.0',
        'python-dotenv>=1.0.0',
        'asyncio>=3.4.3',
        'aiohttp>=3.9.0',
        'PyYAML>=6.0.0',
        'pytest>=7.4.0',
        'python-binance>=1.0.19',
        'websockets>=11.0.0',
        'SQLAlchemy>=2.0.0',
        'loguru>=0.7.0',
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-asyncio',
            'pytest-cov',
            'black',
            'flake8',
            'mypy',
        ]
    },
    entry_points={
        'console_scripts': [
            'trading-bot=app.main:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="Advanced trading bot for automated trading of securities",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    keywords="trading, bot, cryptocurrency, stocks, automation",
    url="https://github.com/yourusername/trading_bot",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires=">=3.9",
)
