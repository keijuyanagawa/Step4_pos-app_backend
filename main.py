from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import os
import hashlib
import uuid
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from db_control.connect_MySQL import engine
from db_control.mymodels_MySQL import (
    CashierMaster, TaxMaster, ProductMaster, 
    TransactionData, TransactionDetail
)

# データベースセッション
Session = sessionmaker(bind=engine)

# セキュリティ
security = HTTPBearer()

# Pydanticモデル
class LoginRequest(BaseModel):
    cashier_code: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    cashier_name: Optional[str] = None
    token: Optional[str] = None

class ProductResponse(BaseModel):
    barcode: str
    product_name: str
    unit_price: int
    tax_code: str
    tax_rate: float
    price_incl_tax: int

class CartItem(BaseModel):
    barcode: str
    product_name: str
    unit_price: int
    quantity: int
    tax_code: str
    tax_rate: float
    subtotal_excl_tax: int
    tax_amount: int
    subtotal_incl_tax: int

class PurchaseRequest(BaseModel):
    store_code: str
    pos_machine_id: str
    cashier_code: str
    cart_items: List[CartItem]

class PurchaseResponse(BaseModel):
    success: bool
    message: str
    transaction_id: Optional[str] = None
    total_amount_excl_tax: Optional[int] = None
    total_tax_amount: Optional[int] = None
    total_amount_incl_tax: Optional[int] = None

app = FastAPI(
    title="簡易POSシステム API",
    description="Tech0 Step4 POSシステムのバックエンドAPI",
    version="1.0.0"
)

# 環境に応じたCORS設定
allowed_origins = []

# 本番環境（Azure）の場合
if os.getenv("AZURE_FUNCTIONS_ENVIRONMENT") or os.getenv("WEBSITE_SITE_NAME"):
    # AzureのフロントエンドURL（NEXTJS_URLまたはFRONTEND_URLを使用）
    frontend_url = os.getenv("NEXTJS_URL") or os.getenv("FRONTEND_URL", "https://app-002-gen10-step3-1-node-oshima36.azurewebsites.net")
    # デバッグ用に複数のURLを許可
    allowed_origins = [
        frontend_url,
        "https://app-002-gen10-step3-1-node-oshima36.azurewebsites.net",
        "https://app-002-gen10-step3-1-node-oshima36.azurewebsites.net/"
    ]
else:
    # ローカル開発環境
    allowed_origins = ["http://localhost:3000"]

print(f"CORS allowed_origins: {allowed_origins}")  # デバッグ用

app.add_middleware(
	CORSMiddleware,
	allow_origins=allowed_origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# ヘルパー関数
def get_db():
    """データベースセッション取得"""
    db = Session()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    """パスワードハッシュ化"""
    return hashlib.sha256(password.encode()).hexdigest()

def calculate_tax_amount(price: int, tax_rate: float) -> int:
    """消費税額計算（切り捨て）"""
    return int(price * tax_rate)

def generate_transaction_id(store_code: str, pos_machine_id: str) -> str:
    """取引ID生成"""
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S")
    return f"{date_str}_{store_code}_{pos_machine_id}_{time_str}"

# APIエンドポイント
@app.get("/")
def read_root():
    return {
        "message": "簡易POSシステム API",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/api/auth/login", response_model=LoginResponse)
def login(request: LoginRequest, db = Depends(get_db)):
    """
    レジ担当者認証
    """
    try:
        # パスワードハッシュ化
        password_hash = hash_password(request.password)
        
        # レジ担当者検索
        cashier = db.query(CashierMaster).filter(
            CashierMaster.cashier_code == request.cashier_code,
            CashierMaster.password_hash == password_hash,
            CashierMaster.is_active == 1
        ).first()
        
        if not cashier:
            return LoginResponse(
                success=False,
                message="レジ担当者コードまたはパスワードが正しくありません"
            )
        
        # 簡易トークン生成（実際のプロダクションではJWTを使用）
        token = f"{request.cashier_code}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return LoginResponse(
            success=True,
            message="ログイン成功",
            cashier_name=cashier.cashier_name,
            token=token
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"認証エラー: {str(e)}")


@app.get("/api/products/{barcode}", response_model=ProductResponse)
def get_product_by_barcode(barcode: str, db = Depends(get_db)):
    """
    バーコードによる商品検索
    """
    try:
        # 商品マスタから検索（税マスタとJOIN）
        result = db.query(ProductMaster, TaxMaster).join(
            TaxMaster, ProductMaster.tax_code == TaxMaster.tax_code
        ).filter(
            ProductMaster.barcode == barcode,
            ProductMaster.is_active == 1,
            TaxMaster.is_active == 1
        ).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="商品がマスタ未登録です")
        
        product, tax = result
        
        # 税込価格計算
        tax_amount = calculate_tax_amount(product.unit_price, tax.tax_rate)
        price_incl_tax = product.unit_price + tax_amount
        
        return ProductResponse(
            barcode=product.barcode,
            product_name=product.product_name,
            unit_price=product.unit_price,
            tax_code=product.tax_code,
            tax_rate=tax.tax_rate,
            price_incl_tax=price_incl_tax
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"商品検索エラー: {str(e)}")

@app.post("/api/purchase", response_model=PurchaseResponse)
def purchase(request: PurchaseRequest, db = Depends(get_db)):
    """
    購入確定
    """
    try:
        # 取引ID生成
        transaction_id = generate_transaction_id(request.store_code, request.pos_machine_id)
        
        # 合計金額計算
        total_amount_excl_tax = sum(item.subtotal_excl_tax for item in request.cart_items)
        total_tax_amount = sum(item.tax_amount for item in request.cart_items)
        total_amount_incl_tax = sum(item.subtotal_incl_tax for item in request.cart_items)
        
        # 取引データ作成
        transaction = TransactionData(
            transaction_id=transaction_id,
            store_code=request.store_code,
            pos_machine_id=request.pos_machine_id,
            cashier_code=request.cashier_code,
            transaction_datetime=datetime.now(),
            total_amount_excl_tax=total_amount_excl_tax,
            total_tax_amount=total_tax_amount,
            total_amount_incl_tax=total_amount_incl_tax
        )
        
        db.add(transaction)
        
        # 取引明細データ作成
        for i, item in enumerate(request.cart_items, 1):
            detail = TransactionDetail(
                detail_id=f"{transaction_id}_{i:03d}",
                transaction_id=transaction_id,
                barcode=item.barcode,
                product_name=item.product_name,
                unit_price=item.unit_price,
                quantity=item.quantity,
                subtotal_excl_tax=item.subtotal_excl_tax,
                tax_code=item.tax_code,
                tax_rate=item.tax_rate,
                tax_amount=item.tax_amount,
                subtotal_incl_tax=item.subtotal_incl_tax
            )
            db.add(detail)
        
        # コミット
        db.commit()
        
        return PurchaseResponse(
            success=True,
            message="購入が完了しました",
            transaction_id=transaction_id,
            total_amount_excl_tax=total_amount_excl_tax,
            total_tax_amount=total_tax_amount,
            total_amount_incl_tax=total_amount_incl_tax
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"購入処理エラー: {str(e)}")

@app.get("/api/health")
def health_check():
    """
    ヘルスチェック
    """
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/api/debug/cashiers")
def debug_cashiers(db = Depends(get_db)):
    """
    デバッグ用: レジ担当者一覧
    """
    try:
        cashiers = db.query(CashierMaster).all()
        return {
            "count": len(cashiers),
            "cashiers": [
                {
                    "cashier_code": c.cashier_code,
                    "cashier_name": c.cashier_name,
                    "is_active": c.is_active
                } for c in cashiers
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/debug/products")
def debug_products(db = Depends(get_db)):
    """
    デバッグ用: 商品マスタ一覧
    """
    try:
        products = db.query(ProductMaster).limit(10).all()
        return {
            "count": len(products),
            "products": [
                {
                    "barcode": p.barcode,
                    "product_name": p.product_name,
                    "unit_price": p.unit_price,
                    "tax_code": p.tax_code
                } for p in products
            ]
        }
    except Exception as e:
        return {"error": str(e)}

# Azureでの起動設定（デバッグ用）
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)


#ダミーコミット