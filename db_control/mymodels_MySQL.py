from sqlalchemy import String, Integer, ForeignKey, DateTime, Numeric, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

# レジ担当者マスタ
class CashierMaster(Base):
    __tablename__ = 'cashier_master'
    
    cashier_code: Mapped[str] = mapped_column(String(20), primary_key=True, comment="レジ担当者コード")
    cashier_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="レジ担当者名")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="パスワードハッシュ")
    is_active: Mapped[bool] = mapped_column(Integer, default=1, comment="有効フラグ(0:無効, 1:有効)")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="作成日時")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新日時")

# 税マスタ
class TaxMaster(Base):
    __tablename__ = 'tax_master'
    
    tax_code: Mapped[str] = mapped_column(String(10), primary_key=True, comment="税区分コード")
    tax_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="税区分名")
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, comment="税率(例: 0.1000)")
    is_active: Mapped[bool] = mapped_column(Integer, default=1, comment="有効フラグ(0:無効, 1:有効)")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="作成日時")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新日時")

# 商品マスタ
class ProductMaster(Base):
    __tablename__ = 'product_master'
    
    barcode: Mapped[str] = mapped_column(String(20), primary_key=True, comment="バーコード（JAN等）")
    product_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="商品名")
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False, comment="単価（税抜）")
    tax_code: Mapped[str] = mapped_column(String(10), ForeignKey("tax_master.tax_code"), nullable=False, comment="税区分コード")
    is_active: Mapped[bool] = mapped_column(Integer, default=1, comment="有効フラグ(0:無効, 1:有効)")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="作成日時")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新日時")

# 取引データ
class TransactionData(Base):
    __tablename__ = 'transaction_data'
    
    transaction_id: Mapped[str] = mapped_column(String(30), primary_key=True, comment="取引ID（YYYYMMDD_店舗_POS機_連番）")
    store_code: Mapped[str] = mapped_column(String(10), nullable=False, comment="店舗コード")
    pos_machine_id: Mapped[str] = mapped_column(String(10), nullable=False, comment="POS機ID")
    cashier_code: Mapped[str] = mapped_column(String(20), ForeignKey("cashier_master.cashier_code"), nullable=False, comment="レジ担当者コード")
    transaction_datetime: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="取引日時")
    total_amount_excl_tax: Mapped[int] = mapped_column(Integer, nullable=False, comment="合計金額（税抜）")
    total_tax_amount: Mapped[int] = mapped_column(Integer, nullable=False, comment="消費税合計額")
    total_amount_incl_tax: Mapped[int] = mapped_column(Integer, nullable=False, comment="合計金額（税込）")
    remarks: Mapped[str] = mapped_column(Text, nullable=True, comment="備考")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="作成日時")

# 取引明細データ
class TransactionDetail(Base):
    __tablename__ = 'transaction_detail'
    
    detail_id: Mapped[str] = mapped_column(String(35), primary_key=True, comment="明細ID（取引ID_連番）")
    transaction_id: Mapped[str] = mapped_column(String(30), ForeignKey("transaction_data.transaction_id"), nullable=False, comment="取引ID")
    barcode: Mapped[str] = mapped_column(String(20), ForeignKey("product_master.barcode"), nullable=False, comment="バーコード")
    product_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="商品名（取引時点）")
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False, comment="単価（税抜・取引時点）")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, comment="数量")
    subtotal_excl_tax: Mapped[int] = mapped_column(Integer, nullable=False, comment="小計（税抜）")
    tax_code: Mapped[str] = mapped_column(String(10), nullable=False, comment="税区分コード（取引時点）")
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, comment="税率（取引時点）")
    tax_amount: Mapped[int] = mapped_column(Integer, nullable=False, comment="消費税額")
    subtotal_incl_tax: Mapped[int] = mapped_column(Integer, nullable=False, comment="小計（税込）")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="作成日時")