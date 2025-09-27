from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# 環境に応じたCORS設定
allowed_origins = []

# 本番環境（Azure）の場合
if os.getenv("AZURE_FUNCTIONS_ENVIRONMENT") or os.getenv("WEBSITE_SITE_NAME"):
    # AzureのフロントエンドURL（NEXTJS_URLまたはFRONTEND_URLを使用）
    frontend_url = os.getenv("NEXTJS_URL") or os.getenv("FRONTEND_URL", "https://app-002-gen10-step3-1-node-oshima36.azurewebsites.net")
    allowed_origins = [frontend_url]
else:
    # ローカル開発環境
    allowed_origins = ["http://localhost:3000"]

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

# Azureでの起動設定（デバッグ用）
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)


#ダミーコミット