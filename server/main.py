from fastapi import FastAPI, Header, HTTPException
import httpx

API_KEY = "7bcd6334-bc2e-4cbf-b9d4-61cb9e868869"

app = FastAPI()

@app.post("start_session")
async def start_session():
	async with httpx.AsyncClient() as client:
		response = await client.get("http://localhost:8080/api/v1/session/start/", headers={"X-API-KEY": API_KEY})
		data = response.json()
	
	return {"message": "Session started", "data": data}
