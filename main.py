from fastapi import FastAPI, Request, Response
import httpx, os

ROUTES = {
    os.getenv("PHONE_NUMBER_ID_AGENT_A"): os.getenv("AGENT_A_URL"),
    os.getenv("PHONE_NUMBER_ID_AGENT_B"): os.getenv("AGENT_B_URL"),
}

app = FastAPI()

@app.get("/whatsapp")
def verify(hub_mode: str = "", hub_challenge: str = "", hub_verify_token: str = ""):
    if hub_verify_token == os.getenv("VERIFY_TOKEN"):
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(status_code=403)

@app.post("/whatsapp")
async def inbound(request: Request):
    raw_body = await request.body()      # reenviamos byte-a-byte
    try:
        data = await request.json()
    except Exception:
        data = {}

    phone_id = None
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            val = change.get("value", {})
            meta = val.get("metadata") or {}
            phone_id = meta.get("phone_number_id") or phone_id

    target = ROUTES.get(phone_id)
    if not target:
        return {"status": "ignored", "reason": "unknown phone_number_id", "phone_id": phone_id}

    headers = {"Content-Type": request.headers.get("content-type", "application/json")}
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(target, content=raw_body, headers=headers)

    return {"status": "ok"}

@app.get("/health")
def health():
    return {"ok": True}
