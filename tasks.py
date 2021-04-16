from argparse import Namespace
from datetime import datetime, timedelta
from distutils.core import run_setup
from os import environ
from pathlib import Path
from typing import List

from codecov import main as codecov_main
from coverage.cmdline import main as coverage_main
from invoke import Context, Exit, task
from mike.driver import deploy as mike_deploy
from twine.cli import dispatch

from actyon.__meta__ import PACKAGE_NAME, PROJECT_NAME, PROJECT_VERSION


TWINE_PASSWORD: str = "TWINE_PASSWORD"
TAR_GZ_WILDCARD: str = f'{PROJECT_NAME}-{{version}}*.gz'
WHL_WILDCARD: str = f'{PACKAGE_NAME}-{{version}}*.whl'

PROJECT_PATH: Path = Path(__file__).parent.resolve()
DIST_PATH: Path = PROJECT_PATH / "dist"


def is_branch(ctx: Context, branch: str):
    current_branch: str = ctx.run("git rev-parse --abbrev-ref HEAD", hide=True).stdout.strip("\n ")
    if current_branch != branch:
        raise Exit(f"invalid branch for this action: {current_branch} (requrired: {branch})", code=1)


@task(aliases=["tests"])
def test(ctx):
    coverage_main(["run", "tests.py"])
    coverage_main(["xml"])


@task
def build(ctx):
    run_setup('setup.py', script_args=['sdist', 'bdist_wheel'])


@task(aliases=["deploy-codecov"])
def deploy_cov(ctx):
    is_branch(ctx, "master")
    coverage_xml: Path = PROJECT_PATH / "coverage.xml"
    if not coverage_xml.exists():
        raise Exit(f"file is missing: {coverage_xml}", code=1)

    age: timedelta = datetime.now() - datetime.fromtimestamp(coverage_xml.stat().st_ctime)
    if age > timedelta(minutes=1):
        print(f"ATTENTION! file is older than 1min: {coverage_xml}")

    codecov_main("--branch", "master")


@task(aliases=["deploy-documentation", "publish-documentation"])
def deploy_doc(ctx, push=False, message=None):
    is_branch(ctx, "master")
    args: Namespace = Namespace(
        alias=["latest"],
        branch="gh-pages",
        config_file="mkdocs.yml",
        force=False,
        ignore=False,
        push=push,
        message=message,
        rebase=True,
        redirect=False,
        remote='origin',
        title=None,
        update_aliases=True,
        version=PROJECT_VERSION,
    )
    mike_deploy(args)


@task(aliases=["deploy-package", "publish-package"])
def deploy_pkg(ctx):
    is_branch(ctx, "master")
    environ["TWINE_USERNAME"] = "__token__"
    if environ.get(TWINE_PASSWORD) is None:
        raise Exit(f"missing environment variable {TWINE_PASSWORD}", code=1)

    tar_gz_wildcard: str = TAR_GZ_WILDCARD.format(version=PROJECT_VERSION)
    tar_gz_assets: List[str] = list(str(p) for p in DIST_PATH.glob(tar_gz_wildcard))
    if len(tar_gz_assets) != 1:
        raise Exit(f"invalid number of assets: dist/{tar_gz_wildcard} (required: 1)", code=1)

    whl_wildcard: str = WHL_WILDCARD.format(version=PROJECT_VERSION)
    whl_assets: List[str] = list(str(p) for p in DIST_PATH.glob(whl_wildcard))
    if len(whl_assets) != 1:
        raise Exit(f"invalid number of assets: dist/{whl_wildcard} (required: 1)", code=1)

    assets: List[str] = tar_gz_assets + whl_assets

    dispatch(['upload', *assets])


@task(aliases=["publish"], pre=[test, build], post=[deploy_cov, deploy_doc, deploy_pkg])
def deploy(ctx):
    pass
