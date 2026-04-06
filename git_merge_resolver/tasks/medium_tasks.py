"""
Medium difficulty task scenarios for the Git Merge Conflict Resolver.

Tasks 3 and 4: Multi-conflict scenarios requiring understanding of semantic
dependencies between conflicts or cross-file consistency.
"""

from __future__ import annotations

from git_merge_resolver.models import ConflictBlock


# ---------------------------------------------------------------------------
# Task 3: function_signature_change
# Scenario: Developer A added a required 'tax_rate' parameter to
# calculate_total() and updated existing call sites. Developer B added new
# invoice processing functions that call calculate_total() with the old sig.
# ---------------------------------------------------------------------------

_TASK3_FILE = """\
\"\"\"
Billing service: invoice generation and total calculation.

Handles creation, validation, and total computation for customer invoices,
supporting multiple line items, tax rates, and currency formatting.
\"\"\"

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional


@dataclass
class LineItem:
    \"\"\"A single billable line item on an invoice.\"\"\"

    description: str
    unit_price: float
    quantity: int
    discount_rate: float = 0.0

    @property
    def subtotal(self) -> float:
        \"\"\"Line item subtotal before any tax.\"\"\"
        return self.unit_price * self.quantity * (1 - self.discount_rate)


@dataclass
class Invoice:
    \"\"\"A customer invoice containing one or more line items.\"\"\"

    invoice_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    line_items: List[LineItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    paid: bool = False
    notes: Optional[str] = None

    def add_line_item(self, item: LineItem) -> None:
        \"\"\"Append a line item to this invoice.\"\"\"
        self.line_items.append(item)


<<<<<<< main
def calculate_total(invoice: Invoice, tax_rate: float) -> float:
    \"\"\"Calculate the total invoice amount including tax.

    Args:
        invoice: The invoice to calculate the total for.
        tax_rate: The applicable tax rate as a fraction (e.g. 0.08 for 8%).

    Returns:
        The total amount including tax, rounded to 2 decimal places.
    \"\"\"
    subtotal = sum(item.subtotal for item in invoice.line_items)
    total = subtotal * (1 + tax_rate)
    return round(total, 2)


def generate_invoice_summary(invoice: Invoice, tax_rate: float) -> dict:
    \"\"\"Generate a summary dict for an invoice including totals.\"\"\"
    subtotal = sum(item.subtotal for item in invoice.line_items)
    total = calculate_total(invoice, tax_rate)
    return {
        "invoice_id": invoice.invoice_id,
        "customer_id": invoice.customer_id,
        "line_item_count": len(invoice.line_items),
        "subtotal": round(subtotal, 2),
        "tax_rate": tax_rate,
        "total": total,
        "created_at": invoice.created_at.isoformat(),
        "paid": invoice.paid,
    }
=======
def calculate_total(invoice: Invoice) -> float:
    \"\"\"Calculate the total invoice amount including a default 8% tax.

    Args:
        invoice: The invoice to calculate the total for.

    Returns:
        The total amount including 8% tax, rounded to 2 decimal places.
    \"\"\"
    subtotal = sum(item.subtotal for item in invoice.line_items)
    total = subtotal * 1.08
    return round(total, 2)


def generate_invoice_summary(invoice: Invoice) -> dict:
    \"\"\"Generate a summary dict for an invoice including totals.\"\"\"
    subtotal = sum(item.subtotal for item in invoice.line_items)
    total = calculate_total(invoice)
    return {
        "invoice_id": invoice.invoice_id,
        "customer_id": invoice.customer_id,
        "line_item_count": len(invoice.line_items),
        "subtotal": round(subtotal, 2),
        "total": total,
        "created_at": invoice.created_at.isoformat(),
        "paid": invoice.paid,
    }


def process_bulk_invoices(invoices: List[Invoice]) -> List[dict]:
    \"\"\"Process a list of invoices and return their summaries.

    Used for batch billing runs at end of billing period.

    Args:
        invoices: List of Invoice objects to process.

    Returns:
        List of summary dicts for each invoice.
    \"\"\"
    return [generate_invoice_summary(inv) for inv in invoices]


def mark_invoices_paid(invoice_ids: List[str], all_invoices: List[Invoice]) -> int:
    \"\"\"Mark specified invoices as paid.

    Args:
        invoice_ids: List of invoice IDs to mark as paid.
        all_invoices: The full list of Invoice objects to update.

    Returns:
        The number of invoices successfully marked as paid.
    \"\"\"
    id_set = set(invoice_ids)
    count = 0
    for inv in all_invoices:
        if inv.invoice_id in id_set and not inv.paid:
            inv.paid = True
            count += 1
    return count
>>>>>>> feature/bulk-invoice-processing


def format_invoice_as_text(invoice: Invoice, tax_rate: float) -> str:
    \"\"\"Render an invoice as a human-readable text block.\"\"\"
    lines = [
        f"INVOICE #{invoice.invoice_id[:8].upper()}",
        f"Customer: {invoice.customer_id}",
        f"Date: {invoice.created_at.strftime('%Y-%m-%d')}",
        "-" * 50,
    ]
    for item in invoice.line_items:
        lines.append(
            f"  {item.description:<30} {item.quantity:>3} x ${item.unit_price:.2f}"
            f"  = ${item.subtotal:.2f}"
        )
    total = calculate_total(invoice, tax_rate)
    lines += ["-" * 50, f"  Tax ({tax_rate*100:.1f}%): included", f"  TOTAL: ${total:.2f}"]
    return "\\n".join(lines)
"""

TASK3_CONFLICT_001_OURS = """\
def calculate_total(invoice: Invoice, tax_rate: float) -> float:
    \"\"\"Calculate the total invoice amount including tax.

    Args:
        invoice: The invoice to calculate the total for.
        tax_rate: The applicable tax rate as a fraction (e.g. 0.08 for 8%).

    Returns:
        The total amount including tax, rounded to 2 decimal places.
    \"\"\"
    subtotal = sum(item.subtotal for item in invoice.line_items)
    total = subtotal * (1 + tax_rate)
    return round(total, 2)


def generate_invoice_summary(invoice: Invoice, tax_rate: float) -> dict:
    \"\"\"Generate a summary dict for an invoice including totals.\"\"\"
    subtotal = sum(item.subtotal for item in invoice.line_items)
    total = calculate_total(invoice, tax_rate)
    return {
        "invoice_id": invoice.invoice_id,
        "customer_id": invoice.customer_id,
        "line_item_count": len(invoice.line_items),
        "subtotal": round(subtotal, 2),
        "tax_rate": tax_rate,
        "total": total,
        "created_at": invoice.created_at.isoformat(),
        "paid": invoice.paid,
    }
"""

TASK3_CONFLICT_001_THEIRS = """\
def calculate_total(invoice: Invoice) -> float:
    \"\"\"Calculate the total invoice amount including a default 8% tax.

    Args:
        invoice: The invoice to calculate the total for.

    Returns:
        The total amount including 8% tax, rounded to 2 decimal places.
    \"\"\"
    subtotal = sum(item.subtotal for item in invoice.line_items)
    total = subtotal * 1.08
    return round(total, 2)


def generate_invoice_summary(invoice: Invoice) -> dict:
    \"\"\"Generate a summary dict for an invoice including totals.\"\"\"
    subtotal = sum(item.subtotal for item in invoice.line_items)
    total = calculate_total(invoice)
    return {
        "invoice_id": invoice.invoice_id,
        "customer_id": invoice.customer_id,
        "line_item_count": len(invoice.line_items),
        "subtotal": round(subtotal, 2),
        "total": total,
        "created_at": invoice.created_at.isoformat(),
        "paid": invoice.paid,
    }


def process_bulk_invoices(invoices: List[Invoice]) -> List[dict]:
    \"\"\"Process a list of invoices and return their summaries.

    Used for batch billing runs at end of billing period.

    Args:
        invoices: List of Invoice objects to process.

    Returns:
        List of summary dicts for each invoice.
    \"\"\"
    return [generate_invoice_summary(inv) for inv in invoices]


def mark_invoices_paid(invoice_ids: List[str], all_invoices: List[Invoice]) -> int:
    \"\"\"Mark specified invoices as paid.

    Args:
        invoice_ids: List of invoice IDs to mark as paid.
        all_invoices: The full list of Invoice objects to update.

    Returns:
        The number of invoices successfully marked as paid.
    \"\"\"
    id_set = set(invoice_ids)
    count = 0
    for inv in all_invoices:
        if inv.invoice_id in id_set and not inv.paid:
            inv.paid = True
            count += 1
    return count
"""

TASK3_CONFLICT_001_GROUND_TRUTH = """\
def calculate_total(invoice: Invoice, tax_rate: float) -> float:
    \"\"\"Calculate the total invoice amount including tax.

    Args:
        invoice: The invoice to calculate the total for.
        tax_rate: The applicable tax rate as a fraction (e.g. 0.08 for 8%).

    Returns:
        The total amount including tax, rounded to 2 decimal places.
    \"\"\"
    subtotal = sum(item.subtotal for item in invoice.line_items)
    total = subtotal * (1 + tax_rate)
    return round(total, 2)


def generate_invoice_summary(invoice: Invoice, tax_rate: float = 0.08) -> dict:
    \"\"\"Generate a summary dict for an invoice including totals.\"\"\"
    subtotal = sum(item.subtotal for item in invoice.line_items)
    total = calculate_total(invoice, tax_rate)
    return {
        "invoice_id": invoice.invoice_id,
        "customer_id": invoice.customer_id,
        "line_item_count": len(invoice.line_items),
        "subtotal": round(subtotal, 2),
        "tax_rate": tax_rate,
        "total": total,
        "created_at": invoice.created_at.isoformat(),
        "paid": invoice.paid,
    }


def process_bulk_invoices(invoices: List[Invoice], tax_rate: float = 0.08) -> List[dict]:
    \"\"\"Process a list of invoices and return their summaries.

    Used for batch billing runs at end of billing period.

    Args:
        invoices: List of Invoice objects to process.
        tax_rate: The applicable tax rate as a fraction (e.g. 0.08 for 8%).

    Returns:
        List of summary dicts for each invoice.
    \"\"\"
    return [generate_invoice_summary(inv, tax_rate) for inv in invoices]


def mark_invoices_paid(invoice_ids: List[str], all_invoices: List[Invoice]) -> int:
    \"\"\"Mark specified invoices as paid.

    Args:
        invoice_ids: List of invoice IDs to mark as paid.
        all_invoices: The full list of Invoice objects to update.

    Returns:
        The number of invoices successfully marked as paid.
    \"\"\"
    id_set = set(invoice_ids)
    count = 0
    for inv in all_invoices:
        if inv.invoice_id in id_set and not inv.paid:
            inv.paid = True
            count += 1
    return count
"""


def get_task3() -> dict:
    """Return the task definition for function_signature_change."""
    conflict_blocks = [
        ConflictBlock(
            conflict_id="conflict_001",
            file_path="src/services/billing.py",
            ours_content=TASK3_CONFLICT_001_OURS,
            theirs_content=TASK3_CONFLICT_001_THEIRS,
            surrounding_context_before=(
                "@dataclass\n"
                "class Invoice:\n"
                "    \"\"\"A customer invoice containing one or more line items.\"\"\"\n"
                "    invoice_id: str = field(default_factory=lambda: str(uuid.uuid4()))\n"
                "    ...\n\n"
                "    def add_line_item(self, item: LineItem) -> None:\n"
                "        \"\"\"Append a line item to this invoice.\"\"\"\n"
                "        self.line_items.append(item)\n\n"
            ),
            surrounding_context_after=(
                "\ndef format_invoice_as_text(invoice: Invoice, tax_rate: float) -> str:\n"
                "    \"\"\"Render an invoice as a human-readable text block.\"\"\"\n"
            ),
            ours_branch_name="main",
            theirs_branch_name="feature/bulk-invoice-processing",
        ),
    ]

    file_contents = {"src/services/billing.py": _TASK3_FILE}
    ground_truths = {"conflict_001": TASK3_CONFLICT_001_GROUND_TRUTH}

    return {
        "task_id": "function_signature_change",
        "task_description": (
            "Someone made tax_rate an explicit parameter in calculate_total() — good change, "
            "makes the function actually reusable across jurisdictions. But the feature branch "
            "added bulk invoice processing functions that call the old signature. "
            "You need to keep the new signature and update the callers. "
            "tax_rate=0.08 is a reasonable default where one is needed."
        ),
        "difficulty": "medium",
        "conflict_blocks": conflict_blocks,
        "file_contents": file_contents,
        "ground_truths": ground_truths,
        "ours_commit_message": "refactor: make tax_rate an explicit parameter in calculate_total for multi-jurisdiction support",
        "theirs_commit_message": "feat: add bulk invoice processing and paid marking utilities",
        "max_steps": 10,
    }


# ---------------------------------------------------------------------------
# Task 4: class_refactor_vs_feature_addition
# Scenario: Developer A extracted password hashing into a PasswordHasher class.
# Developer B added reset_password() and change_password() using old inline logic.
# Conflicts span two files: manager.py and models.py
# ---------------------------------------------------------------------------

_TASK4_MANAGER_FILE = """\
\"\"\"
User authentication manager: handles user creation, authentication,
password management, and session token generation.
\"\"\"

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from typing import Optional

from src.auth.models import User, UserSession

<<<<<<< main
from src.auth.hasher import PasswordHasher

_hasher = PasswordHasher()
=======
_HASH_ITERATIONS = 260_000
_HASH_ALGORITHM = "sha256"
>>>>>>> feature/password-management


class UserManager:
    \"\"\"Manages user accounts, authentication, and session lifecycle.\"\"\"

    def __init__(self, user_store: dict) -> None:
        self._store: dict = user_store

    def create_user(
        self,
        username: str,
        password: str,
        email: str,
        role: str = "viewer",
    ) -> User:
        \"\"\"Create a new user with a securely hashed password.\"\"\"
        if username in self._store:
            raise ValueError(f"Username '{username}' is already taken")
<<<<<<< main
        hashed = _hasher.hash_password(password)
=======
        salt = secrets.token_hex(32)
        hashed = hashlib.pbkdf2_hmac(
            _HASH_ALGORITHM,
            password.encode("utf-8"),
            salt.encode("utf-8"),
            _HASH_ITERATIONS,
        ).hex()
        hashed = f"{salt}${hashed}"
>>>>>>> feature/password-management
        user = User(username=username, password_hash=hashed, email=email, role=role)
        self._store[username] = user
        return user

    def authenticate(self, username: str, password: str) -> Optional[UserSession]:
        \"\"\"Verify credentials and return a session token on success.\"\"\"
        user = self._store.get(username)
        if user is None:
            return None
<<<<<<< main
        if not _hasher.verify_password(password, user.password_hash):
            return None
=======
        salt, stored_hash = user.password_hash.split("$", 1)
        candidate = hashlib.pbkdf2_hmac(
            _HASH_ALGORITHM,
            password.encode("utf-8"),
            salt.encode("utf-8"),
            _HASH_ITERATIONS,
        ).hex()
        if not hmac.compare_digest(candidate, stored_hash):
            return None
>>>>>>> feature/password-management
        token = secrets.token_urlsafe(32)
        session = UserSession(
            username=username,
            token=token,
            expires_at=int(time.time()) + 3600,
        )
        return session

    def reset_password(self, username: str, new_password: str) -> bool:
        \"\"\"Reset a user's password to a new value.

        Args:
            username: The username whose password to reset.
            new_password: The new plaintext password.

        Returns:
            True if reset was successful, False if user not found.
        \"\"\"
        user = self._store.get(username)
        if user is None:
            return False
        salt = secrets.token_hex(32)
        hashed = hashlib.pbkdf2_hmac(
            _HASH_ALGORITHM,
            new_password.encode("utf-8"),
            salt.encode("utf-8"),
            _HASH_ITERATIONS,
        ).hex()
        user.password_hash = f"{salt}${hashed}"
        return True

    def change_password(
        self, username: str, current_password: str, new_password: str
    ) -> bool:
        \"\"\"Change a user's password after verifying the current one.

        Args:
            username: The username requesting the password change.
            current_password: The user's current plaintext password.
            new_password: The desired new plaintext password.

        Returns:
            True if the change succeeded, False if credentials are invalid.
        \"\"\"
        if not self.authenticate(username, current_password):
            return False
        return self.reset_password(username, new_password)
"""

_TASK4_MODELS_FILE = """\
\"\"\"
Authentication domain models.
\"\"\"

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

<<<<<<< main
@dataclass
class User:
    \"\"\"Represents an authenticated user account.\"\"\"

    username: str
    password_hash: str
    email: str
    role: str = "viewer"
    active: bool = True
    mfa_enabled: bool = False
=======
@dataclass
class User:
    \"\"\"Represents a user account.\"\"\"

    username: str
    password_hash: str
    email: str
    role: str = "viewer"
    active: bool = True
>>>>>>> feature/password-management


@dataclass
class UserSession:
    \"\"\"A short-lived authenticated session.\"\"\"

    username: str
    token: str
    expires_at: int
    refresh_token: Optional[str] = None
"""

TASK4_MANAGER_C001_OURS = """\
from src.auth.hasher import PasswordHasher

_hasher = PasswordHasher()
"""
TASK4_MANAGER_C001_THEIRS = """\
_HASH_ITERATIONS = 260_000
_HASH_ALGORITHM = "sha256"
"""
TASK4_MANAGER_C001_GT = """\
from src.auth.hasher import PasswordHasher

_hasher = PasswordHasher()
_HASH_ITERATIONS = 260_000
_HASH_ALGORITHM = "sha256"
"""

TASK4_MANAGER_C002_OURS = """\
        hashed = _hasher.hash_password(password)
"""
TASK4_MANAGER_C002_THEIRS = """\
        salt = secrets.token_hex(32)
        hashed = hashlib.pbkdf2_hmac(
            _HASH_ALGORITHM,
            password.encode("utf-8"),
            salt.encode("utf-8"),
            _HASH_ITERATIONS,
        ).hex()
        hashed = f"{salt}${hashed}"
"""
TASK4_MANAGER_C002_GT = """\
        hashed = _hasher.hash_password(password)
"""

TASK4_MANAGER_C003_OURS = """\
        if not _hasher.verify_password(password, user.password_hash):
            return None
"""
TASK4_MANAGER_C003_THEIRS = """\
        salt, stored_hash = user.password_hash.split("$", 1)
        candidate = hashlib.pbkdf2_hmac(
            _HASH_ALGORITHM,
            password.encode("utf-8"),
            salt.encode("utf-8"),
            _HASH_ITERATIONS,
        ).hex()
        if not hmac.compare_digest(candidate, stored_hash):
            return None
"""
TASK4_MANAGER_C003_GT = """\
        if not _hasher.verify_password(password, user.password_hash):
            return None
"""

TASK4_MODELS_C001_OURS = """\
@dataclass
class User:
    \"\"\"Represents an authenticated user account.\"\"\"

    username: str
    password_hash: str
    email: str
    role: str = "viewer"
    active: bool = True
    mfa_enabled: bool = False
"""
TASK4_MODELS_C001_THEIRS = """\
@dataclass
class User:
    \"\"\"Represents a user account.\"\"\"

    username: str
    password_hash: str
    email: str
    role: str = "viewer"
    active: bool = True
"""
TASK4_MODELS_C001_GT = """\
@dataclass
class User:
    \"\"\"Represents an authenticated user account.\"\"\"

    username: str
    password_hash: str
    email: str
    role: str = "viewer"
    active: bool = True
    mfa_enabled: bool = False
"""


def get_task4() -> dict:
    """Return the task definition for class_refactor_vs_feature_addition."""
    conflict_blocks = [
        ConflictBlock(
            conflict_id="conflict_001",
            file_path="src/auth/manager.py",
            ours_content=TASK4_MANAGER_C001_OURS,
            theirs_content=TASK4_MANAGER_C001_THEIRS,
            surrounding_context_before=(
                "import secrets\nimport time\nfrom typing import Optional\n\n"
                "from src.auth.models import User, UserSession\n\n"
            ),
            surrounding_context_after=(
                "\n\nclass UserManager:\n"
                "    \"\"\"Manages user accounts, authentication, and session lifecycle.\"\"\"\n"
            ),
            ours_branch_name="main",
            theirs_branch_name="feature/password-management",
        ),
        ConflictBlock(
            conflict_id="conflict_002",
            file_path="src/auth/manager.py",
            ours_content=TASK4_MANAGER_C002_OURS,
            theirs_content=TASK4_MANAGER_C002_THEIRS,
            surrounding_context_before=(
                "    def create_user(self, username, password, email, role='viewer'):\n"
                "        if username in self._store:\n"
                "            raise ValueError(f\"Username '{username}' is already taken\")\n"
            ),
            surrounding_context_after=(
                "        user = User(username=username, password_hash=hashed, "
                "email=email, role=role)\n"
                "        self._store[username] = user\n"
                "        return user\n"
            ),
            ours_branch_name="main",
            theirs_branch_name="feature/password-management",
        ),
        ConflictBlock(
            conflict_id="conflict_003",
            file_path="src/auth/manager.py",
            ours_content=TASK4_MANAGER_C003_OURS,
            theirs_content=TASK4_MANAGER_C003_THEIRS,
            surrounding_context_before=(
                "    def authenticate(self, username: str, password: str):\n"
                "        user = self._store.get(username)\n"
                "        if user is None:\n"
                "            return None\n"
            ),
            surrounding_context_after=(
                "        token = secrets.token_urlsafe(32)\n"
                "        session = UserSession(username=username, token=token, "
                "expires_at=int(time.time()) + 3600)\n"
                "        return session\n"
            ),
            ours_branch_name="main",
            theirs_branch_name="feature/password-management",
        ),
        ConflictBlock(
            conflict_id="conflict_004",
            file_path="src/auth/models.py",
            ours_content=TASK4_MODELS_C001_OURS,
            theirs_content=TASK4_MODELS_C001_THEIRS,
            surrounding_context_before=(
                "from dataclasses import dataclass, field\nfrom typing import Optional\n\n"
            ),
            surrounding_context_after=(
                "\n\n@dataclass\nclass UserSession:\n"
                "    \"\"\"A short-lived authenticated session.\"\"\"\n"
                "    username: str\n    token: str\n    expires_at: int\n"
            ),
            ours_branch_name="main",
            theirs_branch_name="feature/password-management",
        ),
    ]

    file_contents = {
        "src/auth/manager.py": _TASK4_MANAGER_FILE,
        "src/auth/models.py": _TASK4_MODELS_FILE,
    }
    ground_truths = {
        "conflict_001": TASK4_MANAGER_C001_GT,
        "conflict_002": TASK4_MANAGER_C002_GT,
        "conflict_003": TASK4_MANAGER_C003_GT,
        "conflict_004": TASK4_MODELS_C001_GT,
    }

    return {
        "task_id": "class_refactor_vs_feature_addition",
        "task_description": (
            "Refactoring conflict across two files. The main branch pulled password hashing "
            "out into a PasswordHasher class — cleaner separation of concerns. The feature "
            "branch added reset_password() and change_password() but duplicated the old "
            "inline PBKDF2 logic instead. New methods should use the hasher class. "
            "Also make sure models.py keeps the mfa_enabled field from main."
        ),
        "difficulty": "medium",
        "conflict_blocks": conflict_blocks,
        "file_contents": file_contents,
        "ground_truths": ground_truths,
        "ours_commit_message": "refactor: extract password hashing into PasswordHasher strategy class",
        "theirs_commit_message": "feat: add reset_password and change_password to UserManager",
        "max_steps": 10,
    }
