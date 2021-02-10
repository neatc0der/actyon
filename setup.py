from pathlib import Path
from setuptools import setup, find_packages
from typing import List

from actyon.__meta__ import PROJECT_NAME, PROJECT_VERSION, REPOSITORY_NAME


def readme() -> str:
    """print long description"""
    with open('README.md') as f:
        return f.read()


def get_requirements(filename: str, base_dir: str = 'requirements') -> List[str]:
    """Load list of dependencies."""
    install_requires = []
    with open(Path(base_dir) / filename) as fp:
        for line in fp:
            stripped_line = line.partition('#')[0].strip()
            if stripped_line:
                install_requires.append(stripped_line)

    return install_requires


setup(
    name=PROJECT_NAME,
    version=PROJECT_VERSION,
    description='Actyon offers an async approach on a multiplexed flux pattern.',
    long_description=readme(),
    long_description_content_type='text/markdown',
    keywords='actyon async multiplex flux',
    url=f'https://github.com/{REPOSITORY_NAME}',
    author='neatc0der',
    author_email='',
    license='MIT',
    python_requires='>=3.8',
    install_requires=get_requirements('prod.txt'),
    setup_requirements=get_requirements('build.txt'),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    packages=find_packages(exclude=['*.tests']),
    package_dir={
        'actyon': 'actyon',
    },
)
