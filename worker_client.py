"""Small async client for the separate AKash Worker service."""
import base64
import os
import aiohttp

WORKER_URL = os.getenv("WORKER_URL", "").rstrip("/")
WORKER_API_KEY = os.getenv("WORKER_API_KEY", "")

class WorkerError(RuntimeError):
    pass

async def worker_request(method, path, *, json_data=None, params=None, timeout=25):
    if not WORKER_URL or not WORKER_API_KEY:
        raise WorkerError("WORKER_URL and WORKER_API_KEY must be set in Render environment variables")
    headers = {"Authorization": f"Bearer {WORKER_API_KEY}"}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.request(method, WORKER_URL + path, headers=headers,
                                       json=json_data, params=params) as response:
                try: payload = await response.json()
                except Exception: payload = {"error": await response.text()}
                if response.status >= 400:
                    raise WorkerError(payload.get("error", f"Worker HTTP {response.status}"))
                return payload
    except aiohttp.ClientError as exc:
        raise WorkerError(f"Worker connection failed: {exc.__class__.__name__}") from exc

async def worker_start(user_id: int, file_name: str, file_bytes: bytes):
    return await worker_request("POST", "/v1/start", json_data={
        "user_id": int(user_id), "file_name": file_name,
        "content_b64": base64.b64encode(file_bytes).decode("ascii")
    })

async def worker_stop(user_id: int, job_id: str):
    return await worker_request("POST", "/v1/stop", json_data={"user_id": int(user_id), "job_id": job_id})

async def worker_jobs(user_id: int):
    return await worker_request("GET", "/v1/jobs", params={"user_id": str(user_id)})

async def worker_logs(user_id: int, file_name: str):
    result = await worker_request("GET", "/v1/logs", params={"user_id": str(user_id), "file_name": file_name})
    return result.get("log", "")


async def worker_all_jobs():
    return await worker_request("GET", "/v1/admin/jobs")
