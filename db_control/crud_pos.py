# -*- coding: utf-8 -*-
"""
POSシステム用CRUD操作
"""

from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from connect_MySQL import engine
from mymodels_MySQL import (
    CashierMaster, TaxMaster, ProductMaster, 
    TransactionData, TransactionDetail
)
import hashlib

# セッション
Session = sessionmaker(bind=engine)

def authenticate_cashier(cashier_code: str, password: str):
    """
    レジ担当者認証
    """
    session = Session()
    try:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cashier = session.query(CashierMaster).filter(
            CashierMaster.cashier_code == cashier_code,
            CashierMaster.password_hash == password_hash,
            CashierMaster.is_active == 1
        ).first()
        return cashier
    finally:
        session.close()

def get_product_by_barcode(barcode: str):
    """
    バーコードで商品検索
    """
    session = Session()
    try:
        result = session.query(ProductMaster, TaxMaster).join(
            TaxMaster, ProductMaster.tax_code == TaxMaster.tax_code
        ).filter(
            ProductMaster.barcode == barcode,
            ProductMaster.is_active == 1,
            TaxMaster.is_active == 1
        ).first()
        return result
    finally:
        session.close()

def save_transaction(transaction_data, transaction_details):
    """
    取引データ・明細保存
    """
    session = Session()
    try:
        session.add(transaction_data)
        for detail in transaction_details:
            session.add(detail)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


