import os
from pathlib import Path
from sqlalchemy import inspect, text
from sqlalchemy.orm import sessionmaker
from db_control.mymodels_MySQL import (
    Base, CashierMaster, TaxMaster, ProductMaster, 
    TransactionData, TransactionDetail
)
from db_control.connect_MySQL import engine
from datetime import datetime
import hashlib


def init_db():
    """
    データベースの初期化
    ローカル実行時は既存テーブルを削除してから再作成
    """
    print("=== データベース初期化開始 ===")
    
    # インスペクターを作成
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    print(f"既存テーブル: {existing_tables}")
    
    # Azure環境かローカル環境かを判定
    is_azure = bool(os.getenv("AZURE_FUNCTIONS_ENVIRONMENT") or os.getenv("WEBSITE_SITE_NAME"))
    
    if not is_azure and existing_tables:
        # ローカル環境の場合、既存テーブルを削除
        print("🔄 ローカル環境: 既存テーブルを削除します...")
        try:
            # 外部キー制約を無効化してテーブル削除
            with engine.connect() as conn:
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
                for table in existing_tables:
                    conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
                conn.commit()
            print("✅ 既存テーブル削除完了")
        except Exception as e:
            print(f"❌ テーブル削除エラー: {e}")
            raise
    
    # テーブル作成
    print("📝 POSシステム用テーブルを作成中...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ テーブル作成完了!")
        
        # 作成されたテーブル一覧を表示
        inspector = inspect(engine)
        new_tables = inspector.get_table_names()
        print(f"作成されたテーブル: {new_tables}")
        
    except Exception as e:
        print(f"❌ テーブル作成エラー: {e}")
        raise
    
    # 初期データ投入
    print("📊 初期データを投入中...")
    insert_sample_data()
    print("✅ データベース初期化完了!")


def insert_sample_data():
    """
    初期データの投入
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. 税マスタの投入
        print("💰 税マスタデータ投入...")
        tax_data = [
            {"tax_code": "T10", "tax_name": "標準税率", "tax_rate": 0.1000},
            {"tax_code": "T08", "tax_name": "軽減税率", "tax_rate": 0.0800},
            {"tax_code": "T00", "tax_name": "非課税", "tax_rate": 0.0000}
        ]
        
        for tax in tax_data:
            existing = session.query(TaxMaster).filter_by(tax_code=tax["tax_code"]).first()
            if not existing:
                session.add(TaxMaster(**tax))
        
        # 2. レジ担当者マスタの投入
        print("👤 レジ担当者マスタデータ投入...")
        # パスワード「password123」のハッシュ化
        password_hash = hashlib.sha256("password123".encode()).hexdigest()
        
        cashier_data = [
            {"cashier_code": "CASHIER001", "cashier_name": "田中太郎", "password_hash": password_hash},
            {"cashier_code": "CASHIER002", "cashier_name": "佐藤花子", "password_hash": password_hash},
            {"cashier_code": "TEST001", "cashier_name": "テスト太郎", "password_hash": password_hash}
        ]
        
        for cashier in cashier_data:
            existing = session.query(CashierMaster).filter_by(cashier_code=cashier["cashier_code"]).first()
            if not existing:
                session.add(CashierMaster(**cashier))
        
        # 3. 商品マスタの投入
        print("🛍️ 商品マスタデータ投入...")
        product_data = [
            {"barcode": "4901234567890", "product_name": "お茶 500ml", "unit_price": 120, "tax_code": "T08"},
            {"barcode": "4901234567891", "product_name": "コーヒー 250ml", "unit_price": 150, "tax_code": "T08"},
            {"barcode": "4901234567892", "product_name": "ボールペン 青", "unit_price": 100, "tax_code": "T10"},
            {"barcode": "4901234567893", "product_name": "ノート A4", "unit_price": 200, "tax_code": "T10"},
            {"barcode": "4901234567894", "product_name": "チョコレート", "unit_price": 180, "tax_code": "T08"},
            {"barcode": "4901234567895", "product_name": "消しゴム", "unit_price": 80, "tax_code": "T10"},
            {"barcode": "4901234567896", "product_name": "水 500ml", "unit_price": 100, "tax_code": "T08"},
            {"barcode": "4901234567897", "product_name": "定規 30cm", "unit_price": 150, "tax_code": "T10"}
        ]
        
        for product in product_data:
            existing = session.query(ProductMaster).filter_by(barcode=product["barcode"]).first()
            if not existing:
                session.add(ProductMaster(**product))
        
        # コミット
        session.commit()
        print("✅ 初期データ投入完了!")
        
        # データ件数確認
        tax_count = session.query(TaxMaster).count()
        cashier_count = session.query(CashierMaster).count()
        product_count = session.query(ProductMaster).count()
        
        print(f"📊 投入データ確認:")
        print(f"   - 税マスタ: {tax_count}件")
        print(f"   - レジ担当者: {cashier_count}件")
        print(f"   - 商品マスタ: {product_count}件")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 初期データ投入エラー: {e}")
        raise
    finally:
        session.close()


# スクリプトとして直接実行された場合のテスト
if __name__ == "__main__":
    print("🚀 データベース初期化スクリプト実行中...")
    init_db()
    print("🎉 完了!")
