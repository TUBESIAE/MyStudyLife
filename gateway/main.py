from fastapi import FastAPI, Request, Depends
import httpx

app = FastAPI()

SERVICE_URLS = {
    "auth": "http://localhost:8000",
    "schedule": "http://localhost:8001",
    "notes": "http://localhost:8002",
    "notify": "http://localhost:8003"
}

@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(service: str, path: str, request: Request):
    if service not in SERVICE_URLS:
        return {"error": "Service not found"}
    url = f"{SERVICE_URLS[service]}/{path}"
    method = request.method
    headers = dict(request.headers)
    data = await request.body()
    async with httpx.AsyncClient() as client:
        resp = await client.request(method, url, headers=headers, content=data)
        return resp.json()

@app.post("/jadwal")
async def create_jadwal(
    jadwal: JadwalSchema,
    user: str = Depends(get_current_user)
):
    pass