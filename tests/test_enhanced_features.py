"""
Test suite for enhanced_features.py (Enhanced Features module).
"""
import unittest
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import enhanced_features

class TestEnhancedFeatures(unittest.TestCase):
    def test_check_dependencies(self):
        result = enhanced_features.check_dependencies()
        self.assertIsInstance(result, dict)

    def test_install_missing_dependencies(self):
        # Should return a bool (may not actually install in test env)
        result = enhanced_features.install_missing_dependencies()
        self.assertIsInstance(result, bool)

    def test_generate_requirements_file(self):
        # Should not raise error
        try:
            enhanced_features.generate_requirements_file()
        except Exception as e:
            self.fail(f"generate_requirements_file() raised {e}")

    def test_run_diagnostics(self):
        result = enhanced_features.run_diagnostics()
        self.assertIsInstance(result, dict)

if __name__ == "__main__":
    unittest.main()
