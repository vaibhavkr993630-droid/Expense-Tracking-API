from app.db import Base
from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, UniqueConstraint


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "category", "month", "year", name="uq_budget_user_category_period"),
    )
