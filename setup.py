from pathlib import Path
from typing import List

from setuptools import find_packages, setup

from actyon.__meta__ import OWNER, PROJECT_NAME, PROJECT_VERSION, REPOSITORY_NAME


HERE: Path = Path(__file__).parent.resolve()
long_description: str = (HERE / "README.md").read_text(encoding='utf-8')


def get_requirements(path: Path) -> List[str]:
    """Load list of dependencies."""
    install_requires = []
    with open(path) as fp:
        for line in fp:
            stripped_line = line.partition('#')[0].strip()
            if stripped_line:
                install_requires.append(stripped_line)

    return install_requires


setup(
    name=PROJECT_NAME,
    version=PROJECT_VERSION,
    description='Actyon offers an async approach on a multiplexed flux pattern.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='actyon async multiplex flux statemachine',
    url=f'https://github.com/{REPOSITORY_NAME}',
    download_url=f'https://github.com/{REPOSITORY_NAME}/archive/{PROJECT_VERSION}.tar.gz',
    author=OWNER,
    author_email='',
    license='MIT',
    python_requires='>=3.8',
    install_requires=get_requirements(HERE / 'requirements' / 'prod.txt'),
#    setup_requirements=get_requirements(HERE / 'requirements' / 'build.txt'),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        "Operating System :: OS Independent",
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    packages=find_packages(exclude=['*.tests']),
    package_dir={
        'actyon': 'actyon',
    },
)
