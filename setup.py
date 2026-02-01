from setuptools import setup, find_packages

setup(
    name="openagent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31",
        "beautifulsoup4>=4.12",
        "pyyaml>=6.0",
        "pydantic>=2.0",
        "chromadb>=0.4.0",
        "sentence-transformers>=2.2",
        "PyMuPDF>=1.23",
        "python-docx>=1.0",
        "Pillow>=10.0",
        "pytesseract>=0.3",
        "duckduckgo-search>=6.0",
        "flask>=3.0",
        "flask-cors>=4.0",
    ],
)
