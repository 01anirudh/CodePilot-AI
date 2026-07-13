import httpx
from typing import Optional
from app.config import settings


class GitHubService:
    """GitHub API client for repository operations."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.GITHUB_TOKEN
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get_repository(self, owner: str, repo: str) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/repos/{owner}/{repo}", headers=self.headers)
            r.raise_for_status()
            return r.json()

    async def get_contents(self, owner: str, repo: str, path: str = "") -> list[dict]:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/contents/{path}",
                headers=self.headers,
            )
            r.raise_for_status()
            return r.json()

    async def get_file_content(self, owner: str, repo: str, path: str) -> str:
        import base64
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/contents/{path}",
                headers=self.headers,
            )
            r.raise_for_status()
            data = r.json()
            if data.get("encoding") == "base64":
                return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            return data.get("content", "")

    async def get_tree(self, owner: str, repo: str, sha: str = "HEAD") -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/git/trees/{sha}?recursive=1",
                headers=self.headers,
            )
            r.raise_for_status()
            return r.json()

    async def create_branch(self, owner: str, repo: str, branch_name: str, from_sha: str) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/repos/{owner}/{repo}/git/refs",
                headers=self.headers,
                json={"ref": f"refs/heads/{branch_name}", "sha": from_sha},
            )
            r.raise_for_status()
            return r.json()

    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/repos/{owner}/{repo}/pulls",
                headers=self.headers,
                json={"title": title, "body": body, "head": head, "base": base},
            )
            r.raise_for_status()
            return r.json()

    async def get_default_branch_sha(self, owner: str, repo: str, branch: str = "main") -> str:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/git/ref/heads/{branch}",
                headers=self.headers,
            )
            r.raise_for_status()
            return r.json()["object"]["sha"]
