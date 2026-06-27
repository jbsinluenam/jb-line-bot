from unittest.mock import MagicMock
from handlers.message import handle_text


def make_client(transactions=None, accounts=None, budgets=None, spent=None, new_balance=None):
    client = MagicMock()
    client.get_transactions.return_value = transactions or []
    client.get_accounts.return_value = accounts or []
    client.get_budgets.return_value = budgets or []
    client.get_spent_by_category.return_value = spent or {}
    client.update_account_balance.return_value = new_balance
    return client


def test_summary_english_keyword():
    client = make_client(
        transactions=[
            {"Type": "income", "Amount": 1000, "Category": "Income"},
            {"Type": "expense", "Amount": 200, "Category": "Food"},
        ],
        accounts=[
            {"Account": "SCB Savings", "Type": "savings", "Balance": "50000", "Group": "Daily"},
        ],
    )
    result = handle_text("summary", client)
    assert "Summary" in result
    assert "1,000" in result
    assert "200" in result
    assert "SCB Savings" in result


def test_summary_thai_keyword():
    client = make_client()
    result = handle_text("สรุป", client)
    assert "Summary" in result


def test_balance_english_keyword():
    client = make_client(
        accounts=[
            {"Account": "SCB Savings", "Type": "savings", "Balance": "50000", "Group": "Daily"},
            {"Account": "KTC ROP", "Type": "credit", "Balance": "397", "Group": "Daily"},
        ]
    )
    result = handle_text("balance", client)
    assert "SCB Savings" in result
    assert "50,000" in result
    assert "KTC ROP" in result


def test_balance_thai_keyword():
    client = make_client()
    result = handle_text("บัญชี", client)
    assert "Balance" in result


def test_expense_nl():
    client = make_client()
    result = handle_text("กาแฟ 65", client)
    assert "บันทึกแล้ว" in result
    assert "65" in result
    assert "Food" in result
    client.append_transaction.assert_called_once()
    call_kwargs = client.append_transaction.call_args[1]
    assert call_kwargs["tx_type"] == "expense"
    assert call_kwargs["amount"] == 65.0
    assert call_kwargs["category"] == "Food"


def test_expense_with_payment():
    client = make_client(new_balance=397.0)
    result = handle_text("กาแฟ 65 ktc", client)
    assert "KTC ROP" in result
    client.update_account_balance.assert_called_once_with("KTC ROP", 65.0)


def test_expense_scb_deducted():
    client = make_client(new_balance=49935.0)
    result = handle_text("กาแฟ 65", client)
    # No payment = SCB Savings deducted
    client.update_account_balance.assert_called_once_with("SCB Savings", -65.0)
    assert "49,935" in result


def test_income_nl():
    client = make_client(new_balance=104000.0)
    result = handle_text("เงินเดือน 50000", client)
    assert "บันทึกแล้ว" in result
    assert "50,000" in result
    assert "Income" in result
    call_kwargs = client.append_transaction.call_args[1]
    assert call_kwargs["tx_type"] == "income"
    assert call_kwargs["amount"] == 50000.0


def test_unrecognized_text():
    client = make_client()
    result = handle_text("สวัสดี", client)
    assert "ไม่เจอ" in result
    client.append_transaction.assert_not_called()
