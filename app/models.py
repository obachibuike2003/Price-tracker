from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(500), nullable=False)
    url = Column(Text, nullable=False)
    store = Column(String(100), nullable=False)
    image_url = Column(Text)
    category = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan",
                                 order_by="PriceHistory.scraped_at")
    alerts = relationship("Alert", back_populates="product", cascade="all, delete-orphan")

    @property
    def current_price(self):
        if self.price_history:
            return self.price_history[-1].price
        return None

    @property
    def lowest_price(self):
        if self.price_history:
            return min(ph.price for ph in self.price_history)
        return None

    @property
    def highest_price(self):
        if self.price_history:
            return max(ph.price for ph in self.price_history)
        return None

    @property
    def price_drop_pct(self):
        if self.highest_price and self.current_price and self.highest_price > 0:
            return round((self.highest_price - self.current_price) / self.highest_price * 100, 1)
        return 0.0

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "store": self.store,
            "image_url": self.image_url,
            "category": self.category,
            "current_price": float(self.current_price) if self.current_price else None,
            "lowest_price": float(self.lowest_price) if self.lowest_price else None,
            "highest_price": float(self.highest_price) if self.highest_price else None,
            "price_drop_pct": self.price_drop_pct,
            "is_active": self.is_active,
        }


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    in_stock = Column(Boolean, default=True, nullable=False)
    scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="price_history")

    def to_dict(self):
        return {
            "price": self.price,
            "currency": self.currency,
            "in_stock": self.in_stock,
            "scraped_at": self.scraped_at.isoformat(),
        }


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    email = Column(String(255), nullable=False)
    target_price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    triggered_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="alerts")
