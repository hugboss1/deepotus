#!/usr/bin/env python3
"""
Tests E2E pour DEEPOTUS Cabinet Vault - Backend APIs
Teste tous les endpoints du Cabinet Vault selon le plan de test.
"""

import requests
import json
import pyotp
import time
from datetime import datetime

class CabinetVaultTester:
    def __init__(self, base_url="https://prophet-ai-memecoin.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.totp_secret = None
        self.mnemonic = None
        self.tests_run = 0
        self.tests_passed = 0

    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Exécute un test API et retourne le résultat"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        self.log(f"🔍 Test {self.tests_run}: {name}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASS - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                self.log(f"❌ FAIL - Expected {expected_status}, got {response.status_code}")
                self.log(f"   Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            self.log(f"❌ ERROR - {str(e)}")
            return False, {}

    def test_admin_login_without_2fa(self):
        """Test 1: Login admin sans 2FA"""
        self.log("\n=== TEST 1: ADMIN LOGIN SANS 2FA ===")
        success, response = self.run_test(
            "Admin Login (sans 2FA)",
            "POST",
            "admin/login",
            200,
            {"password": "deepotus2026"}
        )
        if success and 'token' in response:
            self.token = response['token']
            self.log(f"✅ Token JWT obtenu: {self.token[:20]}...")
            return True
        return False

    def test_2fa_setup(self):
        """Test 2: Setup 2FA via API"""
        self.log("\n=== TEST 2: ACTIVATION 2FA ===")
        
        # D'abord vérifier le statut 2FA
        success, response = self.run_test(
            "2FA Status Check",
            "GET",
            "admin/2fa/status",
            200
        )
        if success:
            self.log(f"2FA Status: {response}")

        # Setup 2FA
        success, response = self.run_test(
            "2FA Setup",
            "POST",
            "admin/2fa/setup",
            200
        )
        if success and 'secret' in response:
            self.totp_secret = response['secret']
            self.log(f"✅ Secret TOTP obtenu: {self.totp_secret}")
            
            # Générer un code TOTP valide
            totp = pyotp.TOTP(self.totp_secret)
            code = totp.now()
            self.log(f"Code TOTP généré: {code}")
            
            # Vérifier le code TOTP
            success, response = self.run_test(
                "2FA Verify",
                "POST",
                "admin/2fa/verify",
                200,
                {"code": code}
            )
            if success:
                self.log("✅ 2FA activée avec succès")
                return True
        return False

    def test_cabinet_vault_status(self):
        """Test 3: Vérifier le statut du Cabinet Vault"""
        self.log("\n=== TEST 3: CABINET VAULT STATUS ===")
        success, response = self.run_test(
            "Cabinet Vault Status",
            "GET",
            "admin/cabinet-vault/status",
            200
        )
        if success:
            self.log(f"Vault Status: {response}")
            return response.get('initialised', False)
        return False

    def test_vault_init(self):
        """Test 4: Initialiser le Cabinet Vault"""
        self.log("\n=== TEST 4: VAULT INITIALIZATION ===")
        success, response = self.run_test(
            "Vault Init",
            "POST",
            "admin/cabinet-vault/init",
            200
        )
        if success and 'mnemonic' in response:
            self.mnemonic = response['mnemonic']
            self.log(f"✅ Mnemonic générée: {self.mnemonic[:50]}...")
            return True
        return False

    def test_vault_unlock(self):
        """Test 5: Déverrouiller le vault avec la mnemonic"""
        self.log("\n=== TEST 5: VAULT UNLOCK ===")
        if not self.mnemonic:
            self.log("❌ Pas de mnemonic disponible")
            return False
            
        success, response = self.run_test(
            "Vault Unlock",
            "POST",
            "admin/cabinet-vault/unlock",
            200,
            {"mnemonic": self.mnemonic}
        )
        if success:
            self.log("✅ Vault déverrouillé avec succès")
            return True
        return False

    def test_vault_list_secrets(self):
        """Test 6: Lister les secrets (doit être vide initialement)"""
        self.log("\n=== TEST 6: LIST SECRETS ===")
        success, response = self.run_test(
            "List Secrets",
            "GET",
            "admin/cabinet-vault/list",
            200
        )
        if success:
            self.log(f"Categories disponibles: {list(response.get('categories', {}).keys())}")
            return True
        return False

    def test_crud_secret(self):
        """Test 7: CRUD d'un secret"""
        self.log("\n=== TEST 7: CRUD SECRET ===")
        
        # Créer un secret
        success, response = self.run_test(
            "Set Secret",
            "PUT",
            "admin/cabinet-vault/secret/llm_custom/OPENAI_API_KEY",
            200,
            {"value": "sk-frontend-test-12345"}
        )
        if not success:
            return False

        # Lire le secret
        success, response = self.run_test(
            "Get Secret",
            "GET",
            "admin/cabinet-vault/secret/llm_custom/OPENAI_API_KEY",
            200
        )
        if success and response.get('value') == 'sk-frontend-test-12345':
            self.log("✅ Secret lu correctement")
        else:
            self.log("❌ Valeur du secret incorrecte")
            return False

        # Rotation du secret
        success, response = self.run_test(
            "Rotate Secret",
            "PUT",
            "admin/cabinet-vault/secret/llm_custom/OPENAI_API_KEY",
            200,
            {"value": "sk-rotated-67890"}
        )
        if success:
            self.log("✅ Secret rotationné")
            return True
        return False

    def test_export_import(self):
        """Test 8: Export et Import"""
        self.log("\n=== TEST 8: EXPORT/IMPORT ===")
        
        # Export
        success, response = self.run_test(
            "Export Vault",
            "POST",
            "admin/cabinet-vault/export",
            200,
            {"passphrase": "MyExportPass2026!"}
        )
        if not success:
            return False
            
        export_data = response
        self.log("✅ Export réussi")

        # Import (test avec bonne passphrase)
        success, response = self.run_test(
            "Import Vault",
            "POST",
            "admin/cabinet-vault/import",
            200,
            {
                "bundle": export_data,
                "passphrase": "MyExportPass2026!",
                "overwrite": True
            }
        )
        if success:
            self.log(f"✅ Import réussi: {response}")
            return True
        return False

    def test_audit_log(self):
        """Test 9: Vérifier l'audit log"""
        self.log("\n=== TEST 9: AUDIT LOG ===")
        success, response = self.run_test(
            "Get Audit Log",
            "GET",
            "admin/cabinet-vault/audit?limit=50",
            200
        )
        if success:
            items = response.get('items', [])
            self.log(f"✅ {len(items)} entrées d'audit trouvées")
            for item in items[:3]:  # Afficher les 3 premières
                self.log(f"   - {item.get('action')} à {item.get('at')}")
            return True
        return False

    def test_vault_lock(self):
        """Test 10: Verrouiller le vault"""
        self.log("\n=== TEST 10: VAULT LOCK ===")
        success, response = self.run_test(
            "Lock Vault",
            "POST",
            "admin/cabinet-vault/lock",
            200
        )
        if success:
            self.log("✅ Vault verrouillé")
            return True
        return False

    def run_all_tests(self):
        """Exécute tous les tests dans l'ordre"""
        self.log("🚀 DÉBUT DES TESTS CABINET VAULT BACKEND")
        self.log(f"Base URL: {self.base_url}")
        
        tests = [
            self.test_admin_login_without_2fa,
            self.test_2fa_setup,
            self.test_cabinet_vault_status,
            self.test_vault_init,
            self.test_vault_unlock,
            self.test_vault_list_secrets,
            self.test_crud_secret,
            self.test_export_import,
            self.test_audit_log,
            self.test_vault_lock,
        ]
        
        for test in tests:
            try:
                result = test()
                if not result:
                    self.log(f"❌ Test {test.__name__} échoué - arrêt des tests")
                    break
                time.sleep(0.5)  # Petite pause entre les tests
            except Exception as e:
                self.log(f"❌ Erreur dans {test.__name__}: {str(e)}")
                break
        
        self.log(f"\n📊 RÉSULTATS: {self.tests_passed}/{self.tests_run} tests réussis")
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = CabinetVaultTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)