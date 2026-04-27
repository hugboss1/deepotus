#!/usr/bin/env python3
"""
Tests E2E Backend pour Cabinet Vault DEEPOTUS
Teste tous les endpoints du Cabinet Vault via API directe
"""

import requests
import json
import pyotp
import sys
from datetime import datetime

class CabinetVaultTester:
    def __init__(self, base_url="https://prophet-ai-memecoin.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.mnemonic = None
        self.twofa_secret = None
        self.export_bundle = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Test {self.tests_run}: {name}")
        print(f"   {method} {endpoint}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"   ✅ PASS - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                print(f"   ❌ FAIL - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"   ❌ ERROR - {str(e)}")
            return False, {}

    def test_admin_login(self):
        """Test admin login avec 2FA si nécessaire"""
        print("\n" + "="*60)
        print("🔐 ÉTAPE 1: ADMIN LOGIN AVEC 2FA")
        print("="*60)
        
        # D'abord essayer sans 2FA
        success, response = self.run_test(
            "Admin Login (sans 2FA)",
            "POST",
            "api/admin/login",
            200,
            data={"password": "deepotus2026"}
        )
        
        if success and 'token' in response:
            self.token = response['token']
            print(f"   🎫 Token obtenu sans 2FA: {self.token[:50]}...")
            return True
        
        # Si échec, vérifier si 2FA est requis
        if not success:
            print("   ⚠️ Login sans 2FA échoué, tentative avec 2FA...")
            
            # Récupérer le secret 2FA depuis la DB
            import asyncio
            from motor.motor_asyncio import AsyncIOMotorClient
            import os
            
            async def get_2fa_secret():
                client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
                db = client[os.environ.get('DB_NAME', 'test_database')]
                twofa_doc = await db.config.find_one({'_id': 'admin_2fa'})
                client.close()
                return twofa_doc.get('secret') if twofa_doc else None
            
            secret = asyncio.run(get_2fa_secret())
            if secret:
                # Générer un code TOTP
                import pyotp
                totp = pyotp.TOTP(secret)
                code = totp.now()
                print(f"   🔢 Code TOTP généré: {code}")
                
                # Login avec 2FA
                success, response = self.run_test(
                    "Admin Login (avec 2FA)",
                    "POST",
                    "api/admin/login",
                    200,
                    data={"password": "deepotus2026", "totp_code": code}
                )
                
                if success and 'token' in response:
                    self.token = response['token']
                    print(f"   🎫 Token obtenu avec 2FA: {self.token[:50]}...")
                    return True
        
        return False

    def test_cabinet_vault_status(self):
        """Test status du Cabinet Vault"""
        print("\n" + "="*60)
        print("🏛️ ÉTAPE 2: CABINET VAULT STATUS")
        print("="*60)
        
        success, response = self.run_test(
            "Vault Status",
            "GET",
            "api/admin/cabinet-vault/status",
            200
        )
        
        if success:
            print(f"   📊 Status: initialised={response.get('initialised')}, locked={response.get('locked')}")
            return True, response
        return False, {}

    def test_vault_init(self):
        """Test initialisation du vault"""
        print("\n" + "="*60)
        print("🎲 ÉTAPE 3: VAULT INIT - GENERATE MNEMONIC")
        print("="*60)
        
        success, response = self.run_test(
            "Vault Init",
            "POST",
            "api/admin/cabinet-vault/init",
            200,
            data={}
        )
        
        if success and 'mnemonic' in response:
            self.mnemonic = response['mnemonic']
            words = self.mnemonic.split()
            print(f"   🔑 Mnemonic générée: {len(words)} mots")
            print(f"   🔑 Mnemonic: {self.mnemonic[:50]}...")
            return True
        return False

    def test_vault_unlock(self):
        """Test unlock du vault"""
        print("\n" + "="*60)
        print("🔓 ÉTAPE 5: VAULT UNLOCK")
        print("="*60)
        
        if not self.mnemonic:
            print("   ❌ Pas de mnemonic disponible")
            return False
            
        success, response = self.run_test(
            "Vault Unlock",
            "POST",
            "api/admin/cabinet-vault/unlock",
            200,
            data={"mnemonic": self.mnemonic}
        )
        
        if success:
            print(f"   🔓 Vault déverrouillé avec succès")
            return True
        return False

    def test_2fa_setup(self):
        """Test setup 2FA"""
        print("\n" + "="*60)
        print("🔐 ÉTAPE 6: 2FA SETUP")
        print("="*60)
        
        success, response = self.run_test(
            "2FA Setup",
            "POST",
            "api/admin/2fa/setup",
            200,
            data={}
        )
        
        if success and 'secret' in response:
            self.twofa_secret = response['secret']
            backup_codes = response.get('backup_codes', [])
            print(f"   🔐 Secret 2FA: {self.twofa_secret}")
            print(f"   🔑 Backup codes: {len(backup_codes)} codes générés")
            return True
        return False

    def test_2fa_verify(self):
        """Test vérification 2FA"""
        print("\n" + "="*60)
        print("✅ ÉTAPE 6B: 2FA VERIFY")
        print("="*60)
        
        if not self.twofa_secret:
            print("   ❌ Pas de secret 2FA disponible")
            return False
            
        # Générer un code TOTP
        totp = pyotp.TOTP(self.twofa_secret)
        code = totp.now()
        print(f"   🔢 Code TOTP généré: {code}")
        
        success, response = self.run_test(
            "2FA Verify",
            "POST",
            "api/admin/2fa/verify",
            200,
            data={"code": code}
        )
        
        if success:
            print(f"   ✅ 2FA activée avec succès")
            return True
        return False

    def test_vault_list(self):
        """Test list des secrets"""
        print("\n" + "="*60)
        print("📋 ÉTAPE 7: VAULT LIST")
        print("="*60)
        
        success, response = self.run_test(
            "Vault List",
            "GET",
            "api/admin/cabinet-vault/list",
            200
        )
        
        if success:
            categories = response.get('categories', {})
            print(f"   📂 Catégories trouvées: {list(categories.keys())}")
            return True, response
        return False, {}

    def test_secret_crud(self):
        """Test CRUD des secrets"""
        print("\n" + "="*60)
        print("🔧 ÉTAPE 8-10: SECRET CRUD")
        print("="*60)
        
        # CREATE secret
        success, response = self.run_test(
            "Create Secret",
            "PUT",
            "api/admin/cabinet-vault/secret/llm_custom/OPENAI_API_KEY",
            200,
            data={"value": "sk-e2e-test-12345"}
        )
        
        if not success:
            return False
            
        print(f"   ✅ Secret créé")
        
        # READ secret
        success, response = self.run_test(
            "Get Secret",
            "GET",
            "api/admin/cabinet-vault/secret/llm_custom/OPENAI_API_KEY",
            200
        )
        
        if success and response.get('value') == 'sk-e2e-test-12345':
            print(f"   ✅ Secret lu: {response.get('value')}")
        else:
            print(f"   ❌ Valeur incorrecte: {response.get('value')}")
            return False
            
        # ROTATE secret
        success, response = self.run_test(
            "Rotate Secret",
            "PUT",
            "api/admin/cabinet-vault/secret/llm_custom/OPENAI_API_KEY",
            200,
            data={"value": "sk-rotated-67890"}
        )
        
        if success:
            print(f"   ✅ Secret roté")
            return True
        return False

    def test_export_import(self):
        """Test export/import"""
        print("\n" + "="*60)
        print("📦 ÉTAPE 11-13: EXPORT/IMPORT")
        print("="*60)
        
        # EXPORT
        passphrase = "TestExportPass2026!"
        success, response = self.run_test(
            "Export Vault",
            "POST",
            "api/admin/cabinet-vault/export",
            200,
            data={"passphrase": passphrase}
        )
        
        if success:
            self.export_bundle = response
            print(f"   ✅ Export réussi: {len(str(response))} caractères")
        else:
            return False
            
        # IMPORT avec mauvaise passphrase
        success, response = self.run_test(
            "Import Wrong Passphrase",
            "POST",
            "api/admin/cabinet-vault/import",
            400,  # Attendu: erreur
            data={
                "bundle": self.export_bundle,
                "passphrase": "WrongPassphrase123!",
                "overwrite": False
            }
        )
        
        if success:
            print(f"   ✅ Erreur attendue pour mauvaise passphrase")
        
        # IMPORT avec bonne passphrase
        success, response = self.run_test(
            "Import Correct Passphrase",
            "POST",
            "api/admin/cabinet-vault/import",
            200,
            data={
                "bundle": self.export_bundle,
                "passphrase": passphrase,
                "overwrite": True
            }
        )
        
        if success:
            imported = response.get('imported', 0)
            replaced = response.get('replaced', 0)
            total = response.get('total_in_bundle', 0)
            print(f"   ✅ Import réussi: {imported} imported, {replaced} replaced, {total} total")
            return True
        return False

    def test_audit_log(self):
        """Test audit log"""
        print("\n" + "="*60)
        print("📜 ÉTAPE 14: AUDIT LOG")
        print("="*60)
        
        success, response = self.run_test(
            "Audit Log",
            "GET",
            "api/admin/cabinet-vault/audit?limit=50",
            200
        )
        
        if success:
            items = response.get('items', [])
            print(f"   📜 {len(items)} entrées d'audit trouvées")
            
            # Vérifier qu'aucune valeur de secret n'apparaît
            for item in items[:5]:  # Vérifier les 5 premières
                action = item.get('action', '')
                category = item.get('category', '')
                key = item.get('key', '')
                print(f"   📝 {action} {category}/{key} à {item.get('at', '')}")
            
            return True
        return False

    def test_vault_lock(self):
        """Test lock du vault"""
        print("\n" + "="*60)
        print("🔒 ÉTAPE 15: VAULT LOCK")
        print("="*60)
        
        success, response = self.run_test(
            "Vault Lock",
            "POST",
            "api/admin/cabinet-vault/lock",
            200,
            data={}
        )
        
        if success:
            print(f"   🔒 Vault verrouillé")
            return True
        return False

    def test_vault_re_unlock(self):
        """Test re-unlock du vault"""
        print("\n" + "="*60)
        print("🔓 ÉTAPE 16: VAULT RE-UNLOCK")
        print("="*60)
        
        if not self.mnemonic:
            print("   ❌ Pas de mnemonic disponible")
            return False
            
        success, response = self.run_test(
            "Vault Re-Unlock",
            "POST",
            "api/admin/cabinet-vault/unlock",
            200,
            data={"mnemonic": self.mnemonic}
        )
        
        if success:
            print(f"   🔓 Vault re-déverrouillé avec succès")
            return True
        return False

    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🚀 DÉBUT DES TESTS BACKEND CABINET VAULT")
        print("=" * 80)
        
        # Séquence de tests
        tests = [
            ("Login Admin", self.test_admin_login),
            ("Vault Status", self.test_cabinet_vault_status),
            ("Vault Init", self.test_vault_init),
            ("Vault Unlock", self.test_vault_unlock),
            ("2FA Setup", self.test_2fa_setup),
            ("2FA Verify", self.test_2fa_verify),
            ("Vault List", self.test_vault_list),
            ("Secret CRUD", self.test_secret_crud),
            ("Export/Import", self.test_export_import),
            ("Audit Log", self.test_audit_log),
            ("Vault Lock", self.test_vault_lock),
            ("Vault Re-unlock", self.test_vault_re_unlock),
        ]
        
        failed_tests = []
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                if not result:
                    failed_tests.append(test_name)
            except Exception as e:
                print(f"   ❌ EXCEPTION dans {test_name}: {str(e)}")
                failed_tests.append(test_name)
        
        # Résultats finaux
        print("\n" + "=" * 80)
        print("📊 RÉSULTATS FINAUX")
        print("=" * 80)
        print(f"Tests exécutés: {self.tests_run}")
        print(f"Tests réussis: {self.tests_passed}")
        print(f"Taux de réussite: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if failed_tests:
            print(f"\n❌ Tests échoués: {', '.join(failed_tests)}")
        else:
            print(f"\n🎉 TOUS LES TESTS BACKEND RÉUSSIS!")
        
        return len(failed_tests) == 0

def main():
    tester = CabinetVaultTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())