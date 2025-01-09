from setuptools import setup, find_packages

setup(
    name="whatsapp_ride_service",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'flask',
        'sqlalchemy',
        'bcrypt',
        'pyjwt',
        'twilio',
        'stripe',
        'python-dotenv',
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov',
            'black',
            'flake8',
        ],
    },
    python_requires='>=3.9',
)
