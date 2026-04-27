#!/usr/bin/env python3
"""
Test complet du backend Cabinet Vault - DEEPOTUS (version pour vault existant)
Teste tous les endpoints selon les spécifications du Sprint 12.3
"""

import requests
import sys
import time
import pyotp
import json
from datetime import datetime
from typing import Optional, Dict, Any

class CabinetVaultTester:
    def __init__(self, base_url: str = "https://prophet-ai-memecoin.preview.emergentagent.com"):
        self.base_url = base_url
        self.admin_token: Optional[str] = None
        self.admin_password = "deepotus2026"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        # Mnemonic de test - on va en générer une nouvelle pour les tests
        self.test_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon art"
        self.twofa_secret = "GHHPTHC7E3UYHCYXPXLMTM5MUI4UWEDO"  # Secret connu de la DB

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log un résultat de test"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASS")
        else:
            print(f"❌ {name}: FAIL - {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    expected_status: int = 200, headers: Optional[Dict] = None) -> tuple[bool, Dict]:
        """Effectue une requête HTTP et vérifie le status"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        req_headers = {'Content-Type': 'application/json'}
        
        if self.admin_token:
            req_headers['Authorization'] = f'Bearer {self.admin_token}'
        
        if headers:
            req_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=req_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=req_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=req_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=req_headers, timeout=30)
            else:
                return False, {"error": f"Méthode HTTP non supportée: {method}"}

            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text, "status_code": response.status_code}

            return success, response_data

        except Exception as e:
            return False, {"error": str(e)}

    def test_admin_login(self) -> bool:
        """Test AUTH ADMIN : POST /api/admin/login avec 2FA"""
        print("\n🔐 Test AUTH ADMIN...")
        
        totp = pyotp.TOTP(self.twofa_secret)
        code = totp.now()
        
        success, response = self.make_request(
            'POST', 
            '/api/admin/login',
            data={"password": self.admin_password, "totp_code": code},
            expected_status=200
        )
        
        if success and 'token' in response:
            self.admin_token = response['token']
            self.log_test("AUTH ADMIN Login with 2FA", True, f"Token reçu avec 2FA: {response['token'][:20]}...")
            return True
        else:
            self.log_test("AUTH ADMIN Login with 2FA", False, f"Échec login avec 2FA: {response}")
            return False

    def test_2fa_guard_without_token(self) -> bool:
        """Test GUARD 2FA : Vérifier que les endpoints Cabinet Vault sont bloqués sans token"""
        print("\n🛡️ Test GUARD 2FA (sans token admin)...")
        
        # Sauvegarder le token et le supprimer temporairement
        saved_token = self.admin_token
        self.admin_token = None
        
        # Test que /status fonctionne sans token (mais nécessite admin)
        success, response = self.make_request('GET', '/api/admin/cabinet-vault/status', expected_status=401)
        self.log_test("Cabinet Vault Status (sans token)", success, "Status bloqué sans token admin")
        
        # Restaurer le token
        self.admin_token = saved_token
        return True

    def test_vault_status(self) -> bool:
        """Test STATUS : GET /api/admin/cabinet-vault/status"""
        print("\n📊 Test VAULT STATUS...")
        
        success, response = self.make_request('GET', '/api/admin/cabinet-vault/status')
        
        if success and 'initialised' in response:
            is_init = response.get('initialised')
            is_locked = response.get('locked')
            self.log_test("Vault Status", True, f"Status: initialisé={is_init}, verrouillé={is_locked}")
            return True
        else:
            self.log_test("Vault Status", False, f"Réponse status incorrecte: {response}")
            return False

    def test_vault_init_already_exists(self) -> bool:
        """Test INIT VAULT déjà existant : POST /api/admin/cabinet-vault/init → 409"""
        print("\n🏦 Test INIT VAULT (déjà existant)...")
        
        success, response = self.make_request('POST', '/api/admin/cabinet-vault/init', expected_status=409)
        
        if success:
            self.log_test("Vault Init Already Exists", True, "Init rejetée car vault déjà existant (409)")
            return True
        else:
            self.log_test("Vault Init Already Exists", False, f"Devrait retourner 409: {response}")
            return False

    def test_vault_unlock_invalid(self) -> bool:
        """Test UNLOCK INVALIDE : POST /unlock avec phrase fausse"""
        print("\n❌ Test VAULT UNLOCK INVALIDE...")
        
        success, response = self.make_request(
            'POST', 
            '/api/admin/cabinet-vault/unlock',
            data={"mnemonic": self.test_mnemonic},
            expected_status=401
        )
        
        if success:
            self.log_test("Vault Unlock Invalid", True, "Phrase incorrecte correctement rejetée (401)")
            return True
        else:
            self.log_test("Vault Unlock Invalid", False, f"Devrait retourner 401: {response}")
            return False

    def test_vault_locked_operations(self) -> bool:
        """Test VAULT LOCKED 423 : Vérifier que les opérations sont bloquées quand vault verrouillé"""
        print("\n🔒 Test VAULT LOCKED OPERATIONS...")
        
        # Tester que les endpoints retournent 423 quand vault verrouillé
        endpoints_to_test = [
            ('GET', '/api/admin/cabinet-vault/list'),
            ('GET', '/api/admin/cabinet-vault/secret/llm_custom/TEST_KEY'),
            ('PUT', '/api/admin/cabinet-vault/secret/llm_custom/TEST_KEY'),
            ('DELETE', '/api/admin/cabinet-vault/secret/llm_custom/TEST_KEY'),
            ('POST', '/api/admin/cabinet-vault/export')
        ]
        
        all_locked = True
        for method, endpoint in endpoints_to_test:
            data = {"value": "test"} if method == 'PUT' else {"passphrase": "test123456789"} if 'export' in endpoint else None
            success, response = self.make_request(method, endpoint, data=data, expected_status=423)
            if success and response.get('detail', {}).get('code') == 'VAULT_LOCKED':
                self.log_test(f"Vault Locked {method} {endpoint}", True, "Correctement verrouillé (423)")
            else:
                self.log_test(f"Vault Locked {method} {endpoint}", False, f"Devrait retourner 423: {response}")
                all_locked = False
        
        return all_locked

    def test_audit_log(self) -> bool:
        """Test AUDIT LOG : GET /audit?limit=50"""
        print("\n📊 Test AUDIT LOG...")
        
        success, response = self.make_request('GET', '/api/admin/cabinet-vault/audit?limit=50')
        
        if success and 'items' in response:
            items = response['items']
            
            # Vérifier qu'on a des événements d'audit
            if len(items) > 0:
                self.log_test("Audit Log", True, f"Audit log avec {len(items)} événements")
                
                # Vérifier les types d'actions
                actions = [item.get('action') for item in items]
                expected_actions = ['init', 'unlock', 'lock']
                found_actions = [action for action in expected_actions if action in actions]
                
                if found_actions:
                    self.log_test("Audit Actions", True, f"Actions trouvées: {found_actions}")
                else:
                    self.log_test("Audit Actions", False, f"Aucune action attendue trouvée: {actions}")
                
                return True
            else:
                self.log_test("Audit Log", False, "Aucun événement d'audit trouvé")
                return False
        else:
            self.log_test("Audit Log", False, f"Échec récupération audit: {response}")
            return False

    def test_audit_invalid_limit(self) -> bool:
        """Test AUDIT INVALID LIMIT : GET /audit?limit=2000 ou /audit?limit=0"""
        print("\n🚫 Test AUDIT INVALID LIMIT...")
        
        # Test limite trop haute
        success, response = self.make_request('GET', '/api/admin/cabinet-vault/audit?limit=2000', expected_status=400)
        if not success:
            self.log_test("Audit Invalid Limit High", False, f"Devrait retourner 400: {response}")
            return False
        
        self.log_test("Audit Invalid Limit High", True, "Limite haute correctement rejetée (400)")
        
        # Test limite trop basse
        success, response = self.make_request('GET', '/api/admin/cabinet-vault/audit?limit=0', expected_status=400)
        if not success:
            self.log_test("Audit Invalid Limit Low", False, f"Devrait retourner 400: {response}")
            return False
        
        self.log_test("Audit Invalid Limit Low", True, "Limite basse correctement rejetée (400)")
        return True

    def test_2fa_status(self) -> bool:
        """Test 2FA STATUS : GET /api/admin/2fa/status"""
        print("\n🔑 Test 2FA STATUS...")
        
        success, response = self.make_request('GET', '/api/admin/2fa/status')
        
        if success and response.get('enabled'):
            self.log_test("2FA Status", True, f"2FA activée, codes backup restants: {response.get('backup_codes_remaining', 0)}")
            return True
        else:
            self.log_test("2FA Status", False, f"2FA devrait être activée: {response}")
            return False

    def test_export_weak_passphrase(self) -> bool:
        """Test EXPORT PASSPHRASE TROP COURTE : POST /export {passphrase: 'short'}"""
        print("\n🚫 Test EXPORT PASSPHRASE FAIBLE...")
        
        success, response = self.make_request(
            'POST', 
            '/api/admin/cabinet-vault/export',
            data={"passphrase": "short"},
            expected_status=422  # Pydantic validation error
        )
        
        if success and 'detail' in response:
            detail = response['detail']
            if isinstance(detail, list) and len(detail) > 0:
                error = detail[0]
                if error.get('type') == 'string_too_short' and 'passphrase' in str(error.get('loc', [])):
                    self.log_test("Export Weak Passphrase", True, "Passphrase faible correctement rejetée (422)")
                    return True
        
        self.log_test("Export Weak Passphrase", False, f"Validation inattendue: {response}")
        return False

    def run_all_tests(self) -> bool:
        """Exécute tous les tests dans l'ordre logique pour un vault existant"""
        print("🚀 Début des tests Cabinet Vault Backend (vault existant)\n")
        
        # 1. Auth admin avec 2FA
        if not self.test_admin_login():
            print("❌ Échec login admin - arrêt des tests")
            return False
        
        # 2. Test guards sans token
        self.test_2fa_guard_without_token()
        
        # 3. Status vault
        self.test_vault_status()
        
        # 4. Test init sur vault existant
        self.test_vault_init_already_exists()
        
        # 5. Test unlock invalide
        self.test_vault_unlock_invalid()
        
        # 6. Test opérations sur vault verrouillé
        self.test_vault_locked_operations()
        
        # 7. Test 2FA status
        self.test_2fa_status()
        
        # 8. Export passphrase faible
        self.test_export_weak_passphrase()
        
        # 9. Audit log
        self.test_audit_log()
        
        # 10. Audit invalid limit
        self.test_audit_invalid_limit()
        
        return True

    def print_summary(self):
        """Affiche le résumé des tests"""
        print(f"\n📊 RÉSUMÉ DES TESTS")
        print(f"Tests exécutés: {self.tests_run}")
        print(f"Tests réussis: {self.tests_passed}")
        print(f"Taux de réussite: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed < self.tests_run:
            print("\n❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['name']}: {result['details']}")

def main():
    """Point d'entrée principal"""
    tester = CabinetVaultTester()
    
    try:
        success = tester.run_all_tests()
        tester.print_summary()
        
        return 0 if success and tester.tests_passed == tester.tests_run else 1
        
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrompus par l'utilisateur")
        return 1
    except Exception as e:
        print(f"\n💥 Erreur inattendue: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())