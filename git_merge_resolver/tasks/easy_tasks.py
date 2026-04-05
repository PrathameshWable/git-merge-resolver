"""
Easy difficulty task scenarios for the Git Merge Conflict Resolver.

Tasks 1 and 2: Single-file conflicts with clear, unambiguous resolutions.
These tasks test basic conflict resolution with minimal ambiguity.
"""

from __future__ import annotations

from typing import Dict, List

from git_merge_resolver.models import ConflictBlock


# ---------------------------------------------------------------------------
# Task 1: simple_variable_rename
# Scenario: Developer A renamed 'price' to 'cost' throughout the calculator
# module. Developer B added a discount calculation feature using the old name.
# ---------------------------------------------------------------------------

TASK1_FILE_WITH_CONFLICTS = """\
"""  # populated below

_TASK1_FILE = """\
\"\"\"
Financial calculator utilities for e-commerce order processing.

Provides functions for computing order totals, applying discounts,
and formatting currency values for display.
\"\"\"

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


def compute_unit_cost(base_cost: float, quantity: int) -> float:
    \"\"\"Compute the per-unit cost given a base cost and quantity.\"\"\"
    if quantity <= 0:
        raise ValueError(f"Quantity must be positive, got {quantity}")
    return base_cost / quantity


def apply_markup(cost: float, markup_rate: float) -> float:
    \"\"\"Apply a markup rate to a cost and return the marked-up value.\"\"\"
    if markup_rate < 0:
        raise ValueError(f"Markup rate cannot be negative, got {markup_rate}")
    return cost * (1 + markup_rate)


<<<<<<< main
def calculate_line_item(cost: float, quantity: int, markup_rate: float = 0.15) -> float:
    \"\"\"Calculate the total line item value with markup applied.\"\"\"
    unit_cost = compute_unit_cost(cost, quantity)
    return apply_markup(unit_cost * quantity, markup_rate)


def format_cost(cost: float, currency: str = "USD") -> str:
    \"\"\"Format a cost value as a currency string.\"\"\"
    rounded = Decimal(str(cost)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{currency} {rounded}"
=======
def calculate_line_item(price: float, quantity: int, markup_rate: float = 0.15) -> float:
    \"\"\"Calculate the total line item value with markup applied.\"\"\"
    unit_cost = compute_unit_cost(price, quantity)
    return apply_markup(unit_cost * quantity, markup_rate)


def format_cost(price: float, currency: str = "USD") -> str:
    \"\"\"Format a price value as a currency string.\"\"\"
    rounded = Decimal(str(price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{currency} {rounded}"


def calculate_discount(price: float, discount_rate: float) -> float:
    \"\"\"Calculate the discounted price after applying a percentage discount.

    Args:
        price: The original price before discount.
        discount_rate: The discount as a fraction (e.g. 0.10 for 10%).

    Returns:
        The price after the discount has been applied.
    \"\"\"
    if not 0.0 <= discount_rate <= 1.0:
        raise ValueError(f"Discount rate must be between 0 and 1, got {discount_rate}")
    return price * (1 - discount_rate)
>>>>>>> feature/add-discount-calculation


def compute_order_total(line_items: list[float], tax_rate: float = 0.08) -> float:
    \"\"\"Compute the total order value including tax.\"\"\"
    subtotal = sum(line_items)
    return subtotal * (1 + tax_rate)
"""

TASK1_CONFLICT_001_OURS = """\
def calculate_line_item(cost: float, quantity: int, markup_rate: float = 0.15) -> float:
    \"\"\"Calculate the total line item value with markup applied.\"\"\"
    unit_cost = compute_unit_cost(cost, quantity)
    return apply_markup(unit_cost * quantity, markup_rate)


def format_cost(cost: float, currency: str = "USD") -> str:
    \"\"\"Format a cost value as a currency string.\"\"\"
    rounded = Decimal(str(cost)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{currency} {rounded}"
"""

TASK1_CONFLICT_001_THEIRS = """\
def calculate_line_item(price: float, quantity: int, markup_rate: float = 0.15) -> float:
    \"\"\"Calculate the total line item value with markup applied.\"\"\"
    unit_cost = compute_unit_cost(price, quantity)
    return apply_markup(unit_cost * quantity, markup_rate)


def format_cost(price: float, currency: str = "USD") -> str:
    \"\"\"Format a price value as a currency string.\"\"\"
    rounded = Decimal(str(price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{currency} {rounded}"


def calculate_discount(price: float, discount_rate: float) -> float:
    \"\"\"Calculate the discounted price after applying a percentage discount.

    Args:
        price: The original price before discount.
        discount_rate: The discount as a fraction (e.g. 0.10 for 10%).

    Returns:
        The price after the discount has been applied.
    \"\"\"
    if not 0.0 <= discount_rate <= 1.0:
        raise ValueError(f"Discount rate must be between 0 and 1, got {discount_rate}")
    return price * (1 - discount_rate)
"""

TASK1_CONFLICT_001_GROUND_TRUTH = """\
def calculate_line_item(cost: float, quantity: int, markup_rate: float = 0.15) -> float:
    \"\"\"Calculate the total line item value with markup applied.\"\"\"
    unit_cost = compute_unit_cost(cost, quantity)
    return apply_markup(unit_cost * quantity, markup_rate)


def format_cost(cost: float, currency: str = "USD") -> str:
    \"\"\"Format a cost value as a currency string.\"\"\"
    rounded = Decimal(str(cost)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{currency} {rounded}"


def calculate_discount(cost: float, discount_rate: float) -> float:
    \"\"\"Calculate the discounted cost after applying a percentage discount.

    Args:
        cost: The original cost before discount.
        discount_rate: The discount as a fraction (e.g. 0.10 for 10%).

    Returns:
        The cost after the discount has been applied.
    \"\"\"
    if not 0.0 <= discount_rate <= 1.0:
        raise ValueError(f"Discount rate must be between 0 and 1, got {discount_rate}")
    return cost * (1 - discount_rate)
"""

TASK1_CONTEXT_BEFORE = """\
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


def compute_unit_cost(base_cost: float, quantity: int) -> float:
    \"\"\"Compute the per-unit cost given a base cost and quantity.\"\"\"
    if quantity <= 0:
        raise ValueError(f"Quantity must be positive, got {quantity}")
    return base_cost / quantity


def apply_markup(cost: float, markup_rate: float) -> float:
    \"\"\"Apply a markup rate to a cost and return the marked-up value.\"\"\"
    if markup_rate < 0:
        raise ValueError(f"Markup rate cannot be negative, got {markup_rate}")
    return cost * (1 + markup_rate)
"""

TASK1_CONTEXT_AFTER = """\

def compute_order_total(line_items: list[float], tax_rate: float = 0.08) -> float:
    \"\"\"Compute the total order value including tax.\"\"\"
    subtotal = sum(line_items)
    return subtotal * (1 + tax_rate)
"""


def get_task1() -> dict:
    """Return the task definition for simple_variable_rename."""
    conflict_blocks = [
        ConflictBlock(
            conflict_id="conflict_001",
            file_path="src/utils/calculator.py",
            ours_content=TASK1_CONFLICT_001_OURS,
            theirs_content=TASK1_CONFLICT_001_THEIRS,
            surrounding_context_before=TASK1_CONTEXT_BEFORE,
            surrounding_context_after=TASK1_CONTEXT_AFTER,
            ours_branch_name="main",
            theirs_branch_name="feature/add-discount-calculation",
        )
    ]

    file_contents = {"src/utils/calculator.py": _TASK1_FILE}
    ground_truths = {"conflict_001": TASK1_CONFLICT_001_GROUND_TRUTH}

    return {
        "task_id": "simple_variable_rename",
        "task_description": (
            "Resolve a variable rename conflict in a financial calculator module. "
            "Developer A renamed the parameter 'price' to 'cost' throughout the file "
            "for semantic clarity. Developer B added a new 'calculate_discount' function "
            "using the old 'price' parameter name. Resolve so that the new function uses "
            "the canonical 'cost' naming convention."
        ),
        "difficulty": "easy",
        "conflict_blocks": conflict_blocks,
        "file_contents": file_contents,
        "ground_truths": ground_truths,
        "ours_commit_message": "refactor: rename 'price' to 'cost' throughout calculator module for semantic clarity",
        "theirs_commit_message": "feat: add calculate_discount function for promotional pricing",
        "max_steps": 5,
    }


# ---------------------------------------------------------------------------
# Task 2: import_and_usage_update
# Scenario: Developer A migrated HTTP client from 'requests' to 'httpx'.
# Developer B added a new API call using the old 'requests' pattern.
# ---------------------------------------------------------------------------

_TASK2_FILE = """\
\"\"\"
HTTP client for the internal data pipeline API.

Wraps the underlying HTTP library to provide a consistent interface
for making authenticated requests to internal microservices.
\"\"\"

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

<<<<<<< main
import httpx
=======
import requests
>>>>>>> feature/add-batch-endpoint

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 30.0
_DEFAULT_BASE_URL = "https://api.internal.example.com/v2"


class PipelineAPIClient:
    \"\"\"Client for the internal data pipeline REST API.\"\"\"

    def __init__(
        self,
        base_url: str = _DEFAULT_BASE_URL,
        api_key: str = "",
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Client-Version": "2.0.0",
        }

    def get_dataset(self, dataset_id: str) -> Dict[str, Any]:
        \"\"\"Fetch metadata for a specific dataset.\"\"\"
        url = f"{self.base_url}/datasets/{dataset_id}"
<<<<<<< main
        response = httpx.get(url, headers=self._headers, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
=======
        response = requests.get(url, headers=self._headers, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def submit_batch_job(
        self,
        dataset_id: str,
        job_config: Dict[str, Any],
        priority: int = 1,
    ) -> Dict[str, Any]:
        \"\"\"Submit a batch processing job for a dataset.

        Args:
            dataset_id: The ID of the dataset to process.
            job_config: Configuration parameters for the batch job.
            priority: Job priority level (1=normal, 2=high, 3=critical).

        Returns:
            A dict containing the job_id and initial status.
        \"\"\"
        url = f"{self.base_url}/datasets/{dataset_id}/jobs"
        payload = {"config": job_config, "priority": priority}
        response = requests.post(
            url,
            headers=self._headers,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
>>>>>>> feature/add-batch-endpoint

    def list_datasets(
        self, page: int = 1, page_size: int = 50
    ) -> Dict[str, Any]:
        \"\"\"List available datasets with pagination.\"\"\"
        url = f"{self.base_url}/datasets"
        params = {"page": page, "page_size": page_size}
        response = httpx.get(
            url, headers=self._headers, params=params, timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
"""

TASK2_CONFLICT_001_OURS = "import httpx\n"
TASK2_CONFLICT_001_THEIRS = "import requests\n"
TASK2_CONFLICT_001_GROUND_TRUTH = "import httpx\n"

TASK2_CONFLICT_002_OURS = """\
        response = httpx.get(url, headers=self._headers, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
"""
TASK2_CONFLICT_002_THEIRS = """\
        response = requests.get(url, headers=self._headers, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def submit_batch_job(
        self,
        dataset_id: str,
        job_config: Dict[str, Any],
        priority: int = 1,
    ) -> Dict[str, Any]:
        \"\"\"Submit a batch processing job for a dataset.

        Args:
            dataset_id: The ID of the dataset to process.
            job_config: Configuration parameters for the batch job.
            priority: Job priority level (1=normal, 2=high, 3=critical).

        Returns:
            A dict containing the job_id and initial status.
        \"\"\"
        url = f"{self.base_url}/datasets/{dataset_id}/jobs"
        payload = {"config": job_config, "priority": priority}
        response = requests.post(
            url,
            headers=self._headers,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
"""
TASK2_CONFLICT_002_GROUND_TRUTH = """\
        response = httpx.get(url, headers=self._headers, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def submit_batch_job(
        self,
        dataset_id: str,
        job_config: Dict[str, Any],
        priority: int = 1,
    ) -> Dict[str, Any]:
        \"\"\"Submit a batch processing job for a dataset.

        Args:
            dataset_id: The ID of the dataset to process.
            job_config: Configuration parameters for the batch job.
            priority: Job priority level (1=normal, 2=high, 3=critical).

        Returns:
            A dict containing the job_id and initial status.
        \"\"\"
        url = f"{self.base_url}/datasets/{dataset_id}/jobs"
        payload = {"config": job_config, "priority": priority}
        response = httpx.post(
            url,
            headers=self._headers,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
"""


def get_task2() -> dict:
    """Return the task definition for import_and_usage_update."""
    conflict_blocks = [
        ConflictBlock(
            conflict_id="conflict_001",
            file_path="src/api/client.py",
            ours_content=TASK2_CONFLICT_001_OURS,
            theirs_content=TASK2_CONFLICT_001_THEIRS,
            surrounding_context_before=(
                "from __future__ import annotations\n\n"
                "import logging\n"
                "from typing import Any, Dict, Optional\n\n"
            ),
            surrounding_context_after=(
                "\nlogger = logging.getLogger(__name__)\n\n"
                "_DEFAULT_TIMEOUT = 30.0\n"
                "_DEFAULT_BASE_URL = \"https://api.internal.example.com/v2\"\n"
            ),
            ours_branch_name="main",
            theirs_branch_name="feature/add-batch-endpoint",
        ),
        ConflictBlock(
            conflict_id="conflict_002",
            file_path="src/api/client.py",
            ours_content=TASK2_CONFLICT_002_OURS,
            theirs_content=TASK2_CONFLICT_002_THEIRS,
            surrounding_context_before=(
                "    def get_dataset(self, dataset_id: str) -> Dict[str, Any]:\n"
                "        \"\"\"Fetch metadata for a specific dataset.\"\"\"\n"
                "        url = f\"{self.base_url}/datasets/{dataset_id}\"\n"
            ),
            surrounding_context_after=(
                "\n    def list_datasets(\n"
                "        self, page: int = 1, page_size: int = 50\n"
                "    ) -> Dict[str, Any]:\n"
                "        \"\"\"List available datasets with pagination.\"\"\"\n"
            ),
            ours_branch_name="main",
            theirs_branch_name="feature/add-batch-endpoint",
        ),
    ]

    file_contents = {"src/api/client.py": _TASK2_FILE}
    ground_truths = {
        "conflict_001": TASK2_CONFLICT_001_GROUND_TRUTH,
        "conflict_002": TASK2_CONFLICT_002_GROUND_TRUTH,
    }

    return {
        "task_id": "import_and_usage_update",
        "task_description": (
            "Resolve conflicts in an HTTP client module where one branch migrated "
            "from 'requests' to 'httpx' for async compatibility, and the other branch "
            "added a new 'submit_batch_job' method using the old 'requests' API. "
            "The resolution must keep 'httpx' as the HTTP library and update the new "
            "method to use 'httpx.post()' instead of 'requests.post()'."
        ),
        "difficulty": "easy",
        "conflict_blocks": conflict_blocks,
        "file_contents": file_contents,
        "ground_truths": ground_truths,
        "ours_commit_message": "refactor: migrate HTTP client from requests to httpx for async support",
        "theirs_commit_message": "feat: add submit_batch_job endpoint to pipeline API client",
        "max_steps": 5,
    }
