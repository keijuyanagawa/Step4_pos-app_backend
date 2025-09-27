from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ローカルのNext.js開発サーバーからのアクセスを許可
allowed_origins = [
	"http://localhost:3000", 
]

app.add_middleware(
	CORSMiddleware,
	allow_origins=allowed_origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

@app.get("/")
def read_root():
	return {"message": "Hello from FastAPI!"}

@app.get("/api/pos")
def get_pos_data():
	return {"items": ["Apple", "Banana", "Cherry"], "total": 1500}