#!/usr/bin/env python3
"""
Test complet des fonctionnalités IMPORT/EXPORT du Cabinet Vault - DEEPOTUS Sprint 12.5
Teste tous les scénarios d'import/export selon les spécifications
"""

import requests
import sys
import time
import pyotp
import json
import base64
from datetime import datetime
from typing import Optional, Dict, Any

class CabinetVaultImportTester:
    def __init__(self, base_url: str = "https://prophet-ai-memecoin.preview.emergentagent.com"):
        self.base_url = base_url
        self.admin_token: Optional[str] = None
        self.admin_password = "deepotus2026"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.vault_mnemonic: Optional[str] = None
        self.twofa_secret = "GHHPTHC7E3UYHCYXPXLMTM5MUI4UWEDO"  # Secret connu
        self.test_bundle: Optional[Dict] = None
        self.test_passphrase = "StrongTestPass123!"

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

    def setup_admin_auth(self) -> bool:
        """Setup authentication admin avec 2FA"""
        print("\n🔐 Setup AUTH ADMIN avec 2FA...")
        
        # Essayer d'abord login simple
        success, response = self.make_request(
            'POST', 
            '/api/admin/login',
            data={"password": self.admin_password},
            expected_status=200
        )
        
        if success and 'token' in response:
            self.admin_token = response['token']
            self.log_test("Admin Auth Setup (sans 2FA)", True, f"Token reçu sans 2FA")
            
            # Maintenant configurer la 2FA
            return self.setup_2fa()
        else:
            # Si 2FA requis, utiliser le secret connu
            if response.get('detail') == '2FA required':
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
                    self.log_test("Admin Auth Setup (avec 2FA)", True, f"Token reçu avec 2FA")
                    return True
                else:
                    self.log_test("Admin Auth Setup", False, f"Échec login avec 2FA: {response}")
                    return False
            else:
                self.log_test("Admin Auth Setup", False, f"Échec login: {response}")
                return False

    def setup_2fa(self) -> bool:
        """Configure la 2FA si pas encore active"""
        print("🔑 Configuration 2FA...")
        
        # Vérifier le statut 2FA
        success, response = self.make_request('GET', '/api/admin/2fa/status')
        if not success:
            self.log_test("2FA Status Check", False, f"Impossible de vérifier le statut 2FA: {response}")
            return False
        
        if response.get('enabled'):
            print("2FA déjà activée")
            self.log_test("2FA Already Enabled", True, "2FA déjà activée")
            return True
        
        # Setup 2FA si pas encore activée
        success, setup_response = self.make_request('POST', '/api/admin/2fa/setup')
        if not success:
            self.log_test("2FA Setup", False, f"Échec setup 2FA: {setup_response}")
            return False
        
        self.twofa_secret = setup_response.get('secret')
        if not self.twofa_secret:
            self.log_test("2FA Setup", False, "Secret 2FA manquant dans la réponse")
            return False
        
        self.log_test("2FA Setup", True, f"Secret 2FA reçu: {self.twofa_secret[:10]}...")
        
        # Générer un code TOTP et vérifier
        totp = pyotp.TOTP(self.twofa_secret)
        code = totp.now()
        
        success, verify_response = self.make_request(
            'POST', 
            '/api/admin/2fa/verify',
            data={"code": code}
        )
        
        if success:
            self.log_test("2FA Verification", True, "2FA activée avec succès")
            return True
        else:
            self.log_test("2FA Verification", False, f"Échec vérification: {verify_response}")
            return False

    def setup_vault(self) -> bool:
        """Setup ou récupération du vault (init si nécessaire, unlock)"""
        print("\n🏦 Setup VAULT...")
        
        # Vérifier le status du vault
        success, status_response = self.make_request('GET', '/api/admin/cabinet-vault/status')
        if not success:
            self.log_test("Vault Status Check", False, f"Impossible de vérifier le status: {status_response}")
            return False
        
        # Si pas initialisé, l'initialiser
        if not status_response.get('initialised'):
            print("Vault non initialisé, initialisation...")
            success, init_response = self.make_request('POST', '/api/admin/cabinet-vault/init')
            if success and 'mnemonic' in init_response:
                self.vault_mnemonic = init_response['mnemonic']
                self.log_test("Vault Init", True, "Vault initialisé avec succès")
            else:
                self.log_test("Vault Init", False, f"Échec init: {init_response}")
                return False
        else:
            self.log_test("Vault Already Initialized", True, "Vault déjà initialisé")
            # Pour les tests, on va utiliser une mnemonic de test connue
            # Mais d'abord on va essayer de re-init pour avoir une mnemonic fraîche
            print("⚠️ Vault déjà initialisé mais mnemonic inconnue - impossible de continuer les tests")
            return False
        
        # Si vault verrouillé, le déverrouiller
        if status_response.get('locked', True) and self.vault_mnemonic:
            success, unlock_response = self.make_request(
                'POST', 
                '/api/admin/cabinet-vault/unlock',
                data={"mnemonic": self.vault_mnemonic}
            )
            
            if success:
                self.log_test("Vault Unlock", True, "Vault déverrouillé pour les tests")
            else:
                self.log_test("Vault Unlock", False, f"Échec unlock: {unlock_response}")
                return False
        
        return True

    def test_export_import_roundtrip(self) -> bool:
        """Test EXPORT → IMPORT ROUND-TRIP complet"""
        print("\n🔄 Test EXPORT → IMPORT ROUND-TRIP...")
        
        test_category = "llm_custom"
        test_key = "OPENAI_API_KEY"
        test_value = "sk-test-roundtrip-12345"
        
        # 1. PUT un secret de test
        success, response = self.make_request(
            'PUT', 
            f'/api/admin/cabinet-vault/secret/{test_category}/{test_key}',
            data={"value": test_value}
        )
        
        if not success:
            self.log_test("Roundtrip - PUT Secret", False, f"Échec PUT: {response}")
            return False
        
        self.log_test("Roundtrip - PUT Secret", True, f"Secret {test_key} créé")
        
        # 2. POST /export avec passphrase
        success, export_response = self.make_request(
            'POST', 
            '/api/admin/cabinet-vault/export',
            data={"passphrase": self.test_passphrase}
        )
        
        if not success or export_response.get('format') != 'deepotus-vault-v1':
            self.log_test("Roundtrip - Export", False, f"Échec export: {export_response}")
            return False
        
        self.test_bundle = export_response
        secrets_count = len(export_response.get('secrets', []))
        self.log_test("Roundtrip - Export", True, f"Export réussi avec {secrets_count} secrets")
        
        # 3. DELETE le secret test
        success, response = self.make_request(
            'DELETE', 
            f'/api/admin/cabinet-vault/secret/{test_category}/{test_key}'
        )
        
        if not success:
            self.log_test("Roundtrip - DELETE Secret", False, f"Échec DELETE: {response}")
            return False
        
        self.log_test("Roundtrip - DELETE Secret", True, "Secret supprimé")
        
        # 4. POST /import avec {bundle, passphrase}
        success, import_response = self.make_request(
            'POST', 
            '/api/admin/cabinet-vault/import',
            data={"bundle": self.test_bundle, "passphrase": self.test_passphrase}
        )
        
        if not success:
            self.log_test("Roundtrip - Import", False, f"Échec import: {import_response}")
            return False
        
        imported = import_response.get('imported', 0)
        if imported >= 1:
            self.log_test("Roundtrip - Import", True, f"Import réussi: {imported} secrets importés")
        else:
            self.log_test("Roundtrip - Import", False, f"Aucun secret importé: {import_response}")
            return False
        
        # 5. GET /secret pour vérifier la valeur
        success, get_response = self.make_request(
            'GET', 
            f'/api/admin/cabinet-vault/secret/{test_category}/{test_key}'
        )
        
        if success and get_response.get('value') == test_value:
            self.log_test("Roundtrip - Verify Value", True, f"Valeur correcte récupérée: {test_value}")
            return True
        else:
            self.log_test("Roundtrip - Verify Value", False, f"Valeur incorrecte: {get_response}")
            return False

    def test_import_wrong_passphrase(self) -> bool:
        """Test IMPORT WRONG PASSPHRASE"""
        print("\n🚫 Test IMPORT WRONG PASSPHRASE...")
        
        if not self.test_bundle:
            self.log_test("Import Wrong Passphrase", False, "Pas de bundle de test disponible")
            return False
        
        wrong_passphrase = "WrongPassphrase!!"
        success, response = self.make_request(
            'POST', 
            '/api/admin/cabinet-vault/import',
            data={"bundle": self.test_bundle, "passphrase": wrong_passphrase},
            expected_status=400
        )
        
        if success and 'detail' in response:
            detail = str(response['detail'])
            if 'decrypt' in detail.lower() or 'passphrase' in detail.lower():
                self.log_test("Import Wrong Passphrase", True, "Mauvaise passphrase correctement rejetée")
                return True
        
        self.log_test("Import Wrong Passphrase", False, f"Erreur inattendue: {response}")
        return False

    def test_import_malformed_bundle(self) -> bool:
        """Test IMPORT MALFORMED BUNDLE"""
        print("\n🚫 Test IMPORT MALFORMED BUNDLE...")
        
        malformed_bundle = {"format": "wrong-format"}
        success, response = self.make_request(
            'POST', 
            '/api/admin/cabinet-vault/import',
            data={"bundle": malformed_bundle, "passphrase": self.test_passphrase},
            expected_status=400
        )
        
        if success and 'detail' in response:
            detail = str(response['detail'])
            if 'unsupported bundle format' in detail.lower():
                self.log_test("Import Malformed Bundle", True, "Bundle malformé correctement rejeté")
                return True
        
        self.log_test("Import Malformed Bundle", False, f"Erreur inattendue: {response}")
        return False

    def test_import_empty_bundle(self) -> bool:
        """Test IMPORT EMPTY BUNDLE"""
        print("\n📭 Test IMPORT EMPTY BUNDLE...")
        
        empty_bundle = {
            "format": "deepotus-vault-v1",
            "kdf": {
                "algo": "PBKDF2-HMAC-SHA512",
                "iterations": 300000,
                "salt": base64.b64encode(b"test_salt_16byte").decode('ascii')
            },
            "secrets": []
        }
        
        success, response = self.make_request(
            'POST', 
            '/api/admin/cabinet-vault/import',
            data={"bundle": empty_bundle, "passphrase": self.test_passphrase}
        )
        
        if success and response.get('imported') == 0 and response.get('total_in_bundle') == 0:
            self.log_test("Import Empty Bundle", True, "Bundle vide traité correctement")
            return True
        else:
            self.log_test("Import Empty Bundle", False, f"Réponse inattendue: {response}")
            return False

    def test_import_collision_skip(self) -> bool:
        """Test IMPORT COLLISION SKIP"""
        print("\n⏭️ Test IMPORT COLLISION SKIP...")
        
        test_category = "llm_custom"
        test_key = "COLLISION_TEST_KEY"
        original_value = "original-value"
        bundle_value = "bundle-value"
        
        # 1. PUT secret original
        success, response = self.make_request(
            'PUT', 
            f'/api/admin/cabinet-vault/secret/{test_category}/{test_key}',
            data={"value": original_value}
        )
        
        if not success:
            self.log_test("Collision Skip - PUT Original", False, f"Échec PUT: {response}")
            return False
        
        # 2. Export pour créer un bundle
        success, export_response = self.make_request(
            'POST', 
            '/api/admin/cabinet-vault/export',
            data={"passphrase": self.test_passphrase}
        )
        
        if not success:
            self.log_test("Collision Skip - Export", False, f"Échec export: {export_response}")
            return False
        
        # 3. Modifier la valeur locale
        success, response = self.make_request(
            'PUT', 
            f'/api/admin/cabinet-vault/secret/{test_category}/{test_key}',
            data={"value": "modified-local-value"}
        )
        
        if not success:
            self.log_test("Collision Skip - Modify Local", False, f"Échec modification: {response}")
            return False
        
        # 4. Import SANS overwrite=true
        success, import_response = self.make_request(
            'POST', 
            '/api/admin/cabinet-vault/import',
            data={"bundle": export_response, "passphrase": self.test_passphrase, "overwrite": False}
        )
        
        if not success:
            self.log_test("Collision Skip - Import", False, f"Échec import: {import_response}")
            return False
        
        skipped = import_response.get('skipped', 0)
        if skipped >= 1:
            self.log_test("Collision Skip - Import", True, f"Collision skip: {skipped} secrets skippés")
        else:
            self.log_test("Collision Skip - Import", False, f"Aucun secret skippé: {import_response}")
            return False
        
        # 5. Vérifier que la valeur live n'a PAS été remplacée
        success, get_response = self.make_request(
            'GET', 
            f'/api/admin/cabinet-vault/secret/{test_category}/{test_key}'
        )
        
        if success and get_response.get('value') == "modified-local-value":
            self.log_test("Collision Skip - Verify No Replace", True, "Valeur locale préservée")
            return True
        else:
            self.log_test("Collision Skip - Verify No Replace", False, f"Valeur incorrecte: {get_response}")
            return False

    def test_import_collision_overwrite(self) -> bool:
        """Test IMPORT COLLISION OVERWRITE"""
        print("\n🔄 Test IMPORT COLLISION OVERWRITE...")
        
        test_category = "llm_custom"
        test_key = "OVERWRITE_TEST_KEY"
        original_value = "original-overwrite-value"
        
        # 1. PUT secret original
        success, response = self.make_request(
            'PUT', 
            f'/api/admin/cabinet-vault/secret/{test_category}/{test_key}',
            data={"value": original_value}
        )
        
        if not success:
            self.log_test("Collision Overwrite - PUT Original", False, f"Échec PUT: {response}")
            return False
        
        # 2. Export pour créer un bundle
        success, export_response = self.make_request(
            'POST', 
            '/api/admin/cabinet-vault/export',
            data={"passphrase": self.test_passphrase}
        )
        
        if not success:
            self.log_test("Collision Overwrite - Export", False, f"Échec export: {export_response}")
            return False
        
        # 3. Modifier la valeur locale
        success, response = self.make_request(
            'PUT', 
            f'/api/admin/cabinet-vault/secret/{test_category}/{test_key}',
            data={"value": "modified-local-overwrite"}
        )
        
        if not success:
            self.log_test("Collision Overwrite - Modify Local", False, f"Échec modification: {response}")
            return False
        
        # 4. Import AVEC overwrite=true
        success, import_response = self.make_request(
            'POST', 
            '/api/admin/cabinet-vault/import',
            data={"bundle": export_response, "passphrase": self.test_passphrase, "overwrite": True}
        )
        
        if not success:
            self.log_test("Collision Overwrite - Import", False, f"Échec import: {import_response}")
            return False
        
        replaced = import_response.get('replaced', 0)
        if replaced >= 1:
            self.log_test("Collision Overwrite - Import", True, f"Collision overwrite: {replaced} secrets remplacés")
        else:
            self.log_test("Collision Overwrite - Import", False, f"Aucun secret remplacé: {import_response}")
            return False
        
        # 5. Vérifier que la valeur live a été remplacée par celle du bundle
        success, get_response = self.make_request(
            'GET', 
            f'/api/admin/cabinet-vault/secret/{test_category}/{test_key}'
        )
        
        if success and get_response.get('value') == original_value:
            self.log_test("Collision Overwrite - Verify Replace", True, "Valeur du bundle restaurée")
            return True
        else:
            self.log_test("Collision Overwrite - Verify Replace", False, f"Valeur incorrecte: {get_response}")
            return False

    def test_import_short_passphrase(self) -> bool:
        """Test IMPORT SHORT PASSPHRASE"""
        print("\n🚫 Test IMPORT SHORT PASSPHRASE...")
        
        if not self.test_bundle:
            self.log_test("Import Short Passphrase", False, "Pas de bundle de test disponible")
            return False
        
        short_passphrase = "short"
        success, response = self.make_request(
            'POST', 
            '/api/admin/cabinet-vault/import',
            data={"bundle": self.test_bundle, "passphrase": short_passphrase},
            expected_status=422
        )
        
        if success and 'detail' in response:
            # Vérifier que c'est bien une erreur de validation Pydantic
            detail = response['detail']
            if isinstance(detail, list) and len(detail) > 0:
                error = detail[0]
                if error.get('type') == 'string_too_short' and 'passphrase' in str(error.get('loc', [])):
                    self.log_test("Import Short Passphrase", True, "Passphrase courte correctement rejetée (422)")
                    return True
        
        self.log_test("Import Short Passphrase", False, f"Erreur inattendue: {response}")
        return False

    def test_import_vault_locked(self) -> bool:
        """Test IMPORT VAULT LOCKED"""
        print("\n🔒 Test IMPORT VAULT LOCKED...")
        
        # 1. Lock le vault
        success, response = self.make_request('POST', '/api/admin/cabinet-vault/lock')
        if not success:
            self.log_test("Import Vault Locked - Lock", False, f"Échec lock: {response}")
            return False
        
        # 2. Tenter import avec vault verrouillé
        if not self.test_bundle:
            self.log_test("Import Vault Locked", False, "Pas de bundle de test disponible")
            return False
        
        success, response = self.make_request(
            'POST', 
            '/api/admin/cabinet-vault/import',
            data={"bundle": self.test_bundle, "passphrase": self.test_passphrase},
            expected_status=423
        )
        
        if success and response.get('detail', {}).get('code') == 'VAULT_LOCKED':
            self.log_test("Import Vault Locked", True, "Import correctement bloqué avec vault verrouillé (423)")
            
            # Re-unlock pour les tests suivants
            if self.vault_mnemonic:
                unlock_success, unlock_response = self.make_request(
                    'POST', 
                    '/api/admin/cabinet-vault/unlock',
                    data={"mnemonic": self.vault_mnemonic}
                )
                if unlock_success:
                    self.log_test("Re-unlock After Lock Test", True, "Vault re-déverrouillé")
                else:
                    self.log_test("Re-unlock After Lock Test", False, f"Échec re-unlock: {unlock_response}")
            
            return True
        else:
            self.log_test("Import Vault Locked", False, f"Devrait retourner 423: {response}")
            return False

    def test_audit_log_import(self) -> bool:
        """Test AUDIT LOG IMPORT"""
        print("\n📊 Test AUDIT LOG IMPORT...")
        
        # Récupérer l'audit log
        success, response = self.make_request('GET', '/api/admin/cabinet-vault/audit?limit=20')
        
        if not success:
            self.log_test("Audit Log Import", False, f"Échec récupération audit: {response}")
            return False
        
        items = response.get('items', [])
        
        # Chercher des entrées d'import
        import_entries = [item for item in items if item.get('action') == 'import']
        import_failed_entries = [item for item in items if item.get('action') == 'import_failed']
        
        if len(import_entries) > 0:
            # Vérifier qu'il y a des métadonnées extra
            import_entry = import_entries[0]
            extra = import_entry.get('extra', {})
            
            has_import_stats = all(key in extra for key in ['imported', 'replaced', 'skipped', 'overwrite'])
            
            if has_import_stats:
                self.log_test("Audit Log Import Success", True, f"Entrée import trouvée avec stats: {extra}")
            else:
                self.log_test("Audit Log Import Success", False, f"Métadonnées manquantes: {extra}")
        else:
            self.log_test("Audit Log Import Success", False, "Aucune entrée d'import trouvée")
        
        if len(import_failed_entries) > 0:
            self.log_test("Audit Log Import Failed", True, f"Entrée import_failed trouvée")
        else:
            self.log_test("Audit Log Import Failed", False, "Aucune entrée import_failed trouvée")
        
        return len(import_entries) > 0

    def test_regression_check(self) -> bool:
        """Test REGRESSION CHECK"""
        print("\n🔍 Test REGRESSION CHECK...")
        
        # 1. GET /list doit fonctionner normalement
        success, list_response = self.make_request('GET', '/api/admin/cabinet-vault/list')
        if not success:
            self.log_test("Regression - List", False, f"Échec list: {list_response}")
            return False
        
        if 'categories' in list_response and 'schema' in list_response:
            self.log_test("Regression - List", True, "List fonctionne normalement")
        else:
            self.log_test("Regression - List", False, f"Structure incorrecte: {list_response}")
            return False
        
        # 2. /api/prophecy?live=true doit marcher (secret_provider cache invalidé)
        success, prophecy_response = self.make_request('GET', '/api/prophecy?live=true')
        if success:
            self.log_test("Regression - Prophecy", True, "Prophecy fonctionne après import")
        else:
            # Prophecy peut échouer pour d'autres raisons, on log mais on ne fail pas le test
            self.log_test("Regression - Prophecy", False, f"Prophecy échec (peut être normal): {prophecy_response}")
        
        return True

    def run_all_import_tests(self) -> bool:
        """Exécute tous les tests d'import/export dans l'ordre logique"""
        print("🚀 Début des tests Cabinet Vault IMPORT/EXPORT\n")
        
        # 1. Setup auth admin
        if not self.setup_admin_auth():
            print("❌ Échec setup auth admin - arrêt des tests")
            return False
        
        # 2. Setup vault
        if not self.setup_vault():
            print("❌ Échec setup vault - arrêt des tests")
            return False
        
        # 3. Test export → import round-trip
        if not self.test_export_import_roundtrip():
            print("❌ Échec round-trip - arrêt des tests")
            return False
        
        # 4. Test import wrong passphrase
        self.test_import_wrong_passphrase()
        
        # 5. Test import malformed bundle
        self.test_import_malformed_bundle()
        
        # 6. Test import empty bundle
        self.test_import_empty_bundle()
        
        # 7. Test import collision skip
        self.test_import_collision_skip()
        
        # 8. Test import collision overwrite
        self.test_import_collision_overwrite()
        
        # 9. Test import short passphrase
        self.test_import_short_passphrase()
        
        # 10. Test import vault locked
        self.test_import_vault_locked()
        
        # 11. Test audit log import
        self.test_audit_log_import()
        
        # 12. Test regression check
        self.test_regression_check()
        
        return True

    def print_summary(self):
        """Affiche le résumé des tests"""
        print(f"\n📊 RÉSUMÉ DES TESTS IMPORT/EXPORT")
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
    tester = CabinetVaultImportTester()
    
    try:
        success = tester.run_all_import_tests()
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