# -*- coding: utf-8 -*-
import os
import tempfile
import unittest

from tzero_stubs import TypeStubGenerator


class TestTypeStubGenerator(unittest.TestCase):
    """Exhaustive tests for AST Type Stub (.pyi) extraction and token reduction."""

    def test_class_and_method_stub(self):
        sample = '''
class BaseService:
    """Base class for services."""
    def run(self) -> None:
        pass

class PaymentGateway(BaseService):
    """Handles credit card and crypto billing."""
    api_key: str
    timeout: int = 45

    def __init__(self, key: str, live_mode: bool = False):
        self.api_key = key
        self.live_mode = live_mode
        self._internal_cache = {}

    @classmethod
    def from_env(cls) -> "PaymentGateway":
        return cls("secret-env-key")

    @property
    def is_active(self) -> bool:
        return True

    def charge(self, amount: float, currency: str = "USD") -> Dict[str, Any]:
        result = self._send_request(amount)
        return {"status": "success", "amount": amount}
'''
        stub = TypeStubGenerator.generate_stub_from_code(sample, file_path="payment.py")

        self.assertIn("class BaseService:", stub)
        self.assertIn("class PaymentGateway(BaseService):", stub)
        self.assertIn("@classmethod", stub)
        self.assertIn("@property", stub)
        self.assertIn("def charge(self, amount: float, currency: str = 'USD') -> Dict[str, Any]: ...", stub)
        self.assertNotIn("self._send_request", stub)
        self.assertNotIn("self._internal_cache", stub)
        self.assertIn("api_key: str", stub)

    def test_inferred_defaults(self):
        sample = '''
def configure_worker(name="worker-1", max_threads=8, timeout=12.5, verbose=True, extra=None):
    print("Setting up worker")
    return {"status": "ok"}
'''
        stub = TypeStubGenerator.generate_stub_from_code(sample)
        self.assertIn("def configure_worker(", stub)
        self.assertIn("name: str = 'worker-1'", stub)
        self.assertIn("max_threads: int = 8", stub)
        self.assertIn("timeout: float = 12.5", stub)
        self.assertIn("verbose: bool = True", stub)
        self.assertIn("extra: Optional[Any] = None", stub)

    def test_args_kwargs_and_kwonly(self):
        sample = '''
def dispatch(handler, *args: str, priority: int = 1, **kwargs: Any) -> bool:
    for a in args:
        handler(a, **kwargs)
    return True
'''
        stub = TypeStubGenerator.generate_stub_from_code(sample)
        self.assertIn("def dispatch(handler, *args: str, priority: int = 1, **kwargs: Any) -> bool: ...", stub)

    def test_token_savings_metric(self):
        sample = '''
class ComplexAlgorithmicService:
    """Enterprise rate-limiting engine with sliding window token buckets."""
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.buckets = {}
        for i in range(100):
            self.buckets[f"key_{i}"] = [0] * 50

    def calculate_sliding_window(self, client_id: str, timestamp: float) -> bool:
        # Long implementation with intensive calculation
        x = 100
        for step in range(100):
            x = (x * 37 + 19) % 1000
            for inner in range(20):
                x = (x ^ inner) & 0xFF
        return x > 500

    def record_metrics(self, data: dict) -> None:
        lines = []
        for k, v in data.items():
            lines.append(f"{k}: {v}")
        serialized = ";".join(lines)
        with open("log.txt", "a") as f:
            f.write(serialized + "\\n")

    def prune_stale_buckets(self, older_than_seconds: float) -> int:
        removed = 0
        now = 1234567.89
        keys_to_delete = []
        for k, timestamps in self.buckets.items():
            valid = [t for t in timestamps if now - t < older_than_seconds]
            if not valid:
                keys_to_delete.append(k)
        for k in keys_to_delete:
            del self.buckets[k]
            removed += 1
        return removed
'''
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write(sample)
            tf_path = tf.name

        try:
            stub, raw_t, stub_t, sav_pct = TypeStubGenerator.generate_stub_file(tf_path)
            self.assertGreater(raw_t, stub_t)
            self.assertGreater(sav_pct, 40.0)
            self.assertTrue(os.path.exists(tf_path.replace(".py", ".pyi")))
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)
            pyi_path = tf_path.replace(".py", ".pyi")
            if os.path.exists(pyi_path):
                os.remove(pyi_path)

    def test_syntax_fallback(self):
        broken_code = "def broken(x\n    return x + 1"
        stub = TypeStubGenerator.generate_stub_from_code(broken_code)
        self.assertIn("Fallback", stub)


if __name__ == "__main__":
    unittest.main()
