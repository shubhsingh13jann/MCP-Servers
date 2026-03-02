from fastmcp import FastMCP
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import os

# -----------------------------
# Initialize MCP Server
# -----------------------------
mcp = FastMCP(name="Expense Tracker")

# -----------------------------
# Database Setup (ABSOLUTE PATH FIX)
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "expenses.db")

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()


# -----------------------------
# Expense Model
# -----------------------------
class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, nullable=True)
    type = Column(String, default="debit")  # debit or credit
    date = Column(DateTime, default=datetime.utcnow)


# Create tables safely
Base.metadata.create_all(engine)


# -----------------------------
# MCP TOOLS
# -----------------------------

@mcp.tool
def add_expense(amount: float, category: str, description: str = "", type: str = "debit"):
    """Add a debit or credit expense."""
    session = Session()
    try:
        expense = Expense(
            amount=amount,
            category=category,
            description=description,
            type=type.lower()
        )
        session.add(expense)
        session.commit()
        return f"Added {type} of ₹{amount} under {category}"
    finally:
        session.close()


@mcp.tool
def list_expenses():
    """List all expenses."""
    session = Session()
    try:
        expenses = session.query(Expense).all()

        if not expenses:
            return "No expenses found."

        result = []
        for e in expenses:
            result.append(
                f"{e.id}. ₹{e.amount} | {e.category} | {e.description} | {e.type}"
            )

        return "\n".join(result)
    finally:
        session.close()


@mcp.tool
def summarize():
    """Get total debit, credit, and balance."""
    session = Session()
    try:
        expenses = session.query(Expense).all()

        total_debit = sum(e.amount for e in expenses if e.type == "debit")
        total_credit = sum(e.amount for e in expenses if e.type == "credit")
        balance = total_credit - total_debit

        return {
            "total_debit": total_debit,
            "total_credit": total_credit,
            "balance": balance
        }
    finally:
        session.close()


@mcp.tool
def delete_expense(expense_id: int):
    """Delete an expense by ID."""
    session = Session()
    try:
        expense = session.query(Expense).filter_by(id=expense_id).first()

        if not expense:
            return "Expense not found."

        session.delete(expense)
        session.commit()
        return f"Deleted expense {expense_id}"
    finally:
        session.close()


@mcp.tool
def edit_expense(
    expense_id: int,
    amount: float = None,
    category: str = None,
    description: str = None,
    type: str = None
):
    """Edit an existing expense."""
    session = Session()
    try:
        expense = session.query(Expense).filter_by(id=expense_id).first()

        if not expense:
            return "Expense not found."

        if amount is not None:
            expense.amount = amount
        if category is not None:
            expense.category = category
        if description is not None:
            expense.description = description
        if type is not None:
            expense.type = type.lower()

        session.commit()
        return f"Updated expense {expense_id}"
    finally:
        session.close()


# -----------------------------
# Start MCP Server
# -----------------------------
if __name__ == "__main__":
    mcp.run()