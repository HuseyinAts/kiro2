#!/bin/bash
# Test Fixes Verification Script
# Run this to verify all test fixes

echo "========================================="
echo "KIRO2 Backend Test Fixes Verification"
echo "========================================="
echo ""

cd "$(dirname "$0")"

echo "✅ Testing Fixed Files..."
echo ""

echo "1. Testing test_kvkk_consent.py (3 fixes)..."
python -m pytest tests/unit/test_kvkk_consent.py::TestKVKKConsentModel::test_consent_model_creation \
                 tests/unit/test_kvkk_consent.py::TestKVKKConsentModel::test_consent_model_optional_fields \
                 tests/unit/test_kvkk_consent.py::TestKVKKConsentModel::test_consent_withdrawal_fields \
                 -v --tb=short
echo ""

echo "2. Testing test_item_selection_optimizer.py (1 fix)..."
python -m pytest tests/unit/test_item_selection_optimizer.py::TestExposureControl::test_disable_overexposed_items \
                 -v --tb=short
echo ""

echo "⏳ Testing Expected-To-Pass Files..."
echo ""

echo "3. Testing test_learning_path_auth_unit.py (password hashing)..."
python -m pytest tests/unit/test_learning_path_auth_unit.py::TestPasswordHashing -v --tb=short
echo ""

echo "📊 Summary Statistics..."
echo ""

python -m pytest tests/unit/test_kvkk_consent.py \
                 tests/unit/test_item_selection_optimizer.py \
                 tests/unit/test_learning_path_auth_unit.py::TestPasswordHashing \
                 -v --tb=no --no-header

echo ""
echo "========================================="
echo "Verification Complete"
echo "========================================="
