"""Setup script for WhatsApp Ride Service."""

from setuptools import setup, find_packages

setup(
    name="whatsapp_ride_service",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "flask",
        "sqlalchemy",
        "python-dotenv",
        "twilio",
        "pyjwt",
        "geopy",
        "stripe",
        "phonenumbers",
    ],
    extras_require={"dev": ["pytest", "flake8", "black", "mypy"]},
    python_requires=">=3.8",
)
