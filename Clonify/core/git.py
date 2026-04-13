import asyncio
import shlex
from typing import Tuple

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

import config
from ..logging import LOGGER


def install_req(cmd: str) -> Tuple[str, str, int, int]:
    async def install_requirements():
        args = shlex.split(cmd)
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return (
            stdout.decode("utf-8", "replace").strip(),
            stderr.decode("utf-8", "replace").strip(),
            process.returncode,
            process.pid,
        )

    return asyncio.get_event_loop().run_until_complete(install_requirements())


def git():
    REPO_LINK = config.UPSTREAM_REPO

    # 🔐 Token handling
    if config.GIT_TOKEN:
        try:
            GIT_USERNAME = REPO_LINK.split("com/")[1].split("/")[0]
            TEMP_REPO = REPO_LINK.split("https://")[1]
            UPSTREAM_REPO = f"https://{GIT_USERNAME}:{config.GIT_TOKEN}@{TEMP_REPO}"
        except Exception:
            UPSTREAM_REPO = REPO_LINK
    else:
        UPSTREAM_REPO = REPO_LINK

    try:
        # ✅ Check if repo exists
        repo = Repo()
        origin = repo.remotes.origin

        LOGGER(__name__).info("Git repo found, checking for updates...")

        try:
            origin.fetch()
            origin.pull()
            LOGGER(__name__).info("Successfully updated from upstream")
        except GitCommandError as e:
            LOGGER(__name__).info(f"Update failed: {e}")

    except InvalidGitRepositoryError:
        # ❌ Render case — no .git folder
        LOGGER(__name__).info("No git repo detected (Render deploy), skipping git setup...")
        return

    except Exception as e:
        LOGGER(__name__).info(f"Git error skipped: {e}")
        return
