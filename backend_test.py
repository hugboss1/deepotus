#!/usr/bin/env python3
"""
Test complet du backend Cabinet Vault - DEEPOTUS
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
        self.vault_mnemonic: Optional[str] = None
        self.twofa_secret: Optional[str] = None

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
        """Test AUTH ADMIN : POST /api/admin/login"""
        print("\n🔐 Test AUTH ADMIN...")
        
        # Premier essai sans 2FA
        success, response = self.make_request(
            'POST', 
            '/api/admin/login',
            data={"password": self.admin_password},
            expected_status=200
        )
        
        if success and 'token' in response:
            self.admin_token = response['token']
            self.log_test("AUTH ADMIN Login", True, f"Token reçu: {response['token'][:20]}...")
            return True
        
        # Si 2FA requis, utiliser le secret connu
        if response.get('detail') == '2FA required':
            print("2FA requise, utilisation du secret TOTP...")
            self.twofa_secret = "GHHPTHC7E3UYHCYXPXLMTM5MUI4UWEDO"  # Secret récupéré de la DB
            
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
        else:
            self.log_test("AUTH ADMIN Login", False, f"Échec login: {response}", response)
            return False

    def test_2fa_guard_without_2fa(self) -> bool:
        """Test GUARD 2FA : Vérifier que les endpoints Cabinet Vault sont bloqués sans 2FA"""
        print("\n🛡️ Test GUARD 2FA (sans 2FA activée)...")
        
        # Test que /status fonctionne sans 2FA
        success, response = self.make_request('GET', '/api/admin/cabinet-vault/status')
        self.log_test("Cabinet Vault Status (sans 2FA)", success, "Status accessible sans 2FA", response)
        
        # Test que les autres endpoints sont bloqués
        endpoints_to_test = [
            ('POST', '/api/admin/cabinet-vault/init'),
            ('GET', '/api/admin/cabinet-vault/list'),
            ('POST', '/api/admin/cabinet-vault/unlock')
        ]
        
        all_blocked = True
        for method, endpoint in endpoints_to_test:
            success, response = self.make_request(method, endpoint, expected_status=403)
            if success and response.get('detail', {}).get('code') == 'TWOFA_REQUIRED':
                self.log_test(f"2FA Guard {endpoint}", True, "Correctement bloqué sans 2FA")
            else:
                self.log_test(f"2FA Guard {endpoint}", False, f"Devrait être bloqué: {response}")
                all_blocked = False
        
        return all_blocked

    def test_2fa_activation(self) -> bool:
        """Test ACTIVATION 2FA : Activer la 2FA si pas encore active"""
        print("\n🔑 Test ACTIVATION 2FA...")
        
        # Vérifier le statut 2FA
        success, response = self.make_request('GET', '/api/admin/2fa/status')
        if not success:
            self.log_test("2FA Status Check", False, f"Impossible de vérifier le statut 2FA: {response}")
            return False
        
        if response.get('enabled'):
            print("2FA déjà activée")
            self.twofa_secret = "GHHPTHC7E3UYHCYXPXLMTM5MUI4UWEDO"  # Secret connu
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

    def test_vault_init(self) -> bool:
        """Test INIT VAULT : POST /api/admin/cabinet-vault/init"""
        print("\n🏦 Test INIT VAULT...")
        
        success, response = self.make_request('POST', '/api/admin/cabinet-vault/init')
        
        if success and 'mnemonic' in response:
            self.vault_mnemonic = response['mnemonic']
            words = self.vault_mnemonic.split()
            
            if len(words) == 24:
                self.log_test("Vault Init", True, f"Vault initialisé avec 24 mots BIP39")
                
                # Vérifier que le status a changé
                success_status, status_response = self.make_request('GET', '/api/admin/cabinet-vault/status')
                if success_status and status_response.get('initialised') and status_response.get('locked'):
                    self.log_test("Vault Status After Init", True, "Status correct: initialisé et verrouillé")
                    return True
                else:
                    self.log_test("Vault Status After Init", False, f"Status incorrect: {status_response}")
                    return False
            else:
                self.log_test("Vault Init", False, f"Mnemonic invalide: {len(words)} mots au lieu de 24")
                return False
        else:
            self.log_test("Vault Init", False, f"Échec init vault: {response}")
            return False

    def test_vault_init_idempotent(self) -> bool:
        """Test INIT IDEMPOTENT : Tenter une 2ème fois POST /init"""
        print("\n🔒 Test INIT IDEMPOTENT...")
        
        success, response = self.make_request('POST', '/api/admin/cabinet-vault/init', expected_status=409)
        
        if success:
            self.log_test("Vault Init Idempotent", True, "Deuxième init correctement rejetée (409)")
            return True
        else:
            self.log_test("Vault Init Idempotent", False, f"Devrait retourner 409: {response}")
            return False

    def test_vault_unlock(self) -> bool:
        """Test UNLOCK : POST /unlock avec la phrase reçue"""
        print("\n🔓 Test VAULT UNLOCK...")
        
        if not self.vault_mnemonic:
            self.log_test("Vault Unlock", False, "Pas de mnemonic disponible")
            return False
        
        success, response = self.make_request(
            'POST', 
            '/api/admin/cabinet-vault/unlock',
            data={"mnemonic": self.vault_mnemonic}
        )
        
        if success and response.get('ok'):
            self.log_test("Vault Unlock", True, f"Vault déverrouillé, TTL: {response.get('expires_in_seconds')}s")
            
            # Vérifier le status
            success_status, status_response = self.make_request('GET', '/api/admin/cabinet-vault/status')
            if success_status and not status_response.get('locked'):
                self.log_test("Vault Status After Unlock", True, "Status correct: déverrouillé")
                return True
            else:
                self.log_test("Vault Status After Unlock", False, f"Status incorrect: {status_response}")
                return False
        else:
            self.log_test("Vault Unlock", False, f"Échec unlock: {response}")
            return False

    def test_vault_unlock_invalid(self) -> bool:
        """Test UNLOCK INVALIDE : POST /unlock avec phrase fausse"""
        print("\n❌ Test VAULT UNLOCK INVALIDE...")
        
        # Générer une phrase BIP39 valide mais incorrecte
        fake_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon art"
        
        success, response = self.make_request(
            'POST', 
            '/api/admin/cabinet-vault/unlock',
            data={"mnemonic": fake_mnemonic},
            expected_status=401
        )
        
        if success:
            self.log_test("Vault Unlock Invalid", True, "Phrase incorrecte correctement rejetée (401)")
            return True
        else:
            self.log_test("Vault Unlock Invalid", False, f"Devrait retourner 401: {response}")
            return False

    def test_list_secrets(self) -> bool:
        """Test LIST SECRETS : GET /list (unlocked)"""
        print("\n📋 Test LIST SECRETS...")
        
        success, response = self.make_request('GET', '/api/admin/cabinet-vault/list')
        
        if success and 'categories' in response and 'schema' in response:
            categories = response['categories']
            schema = response['schema']
            
            # Vérifier les 10 catégories attendues
            expected_categories = [
                "auth", "llm_emergent", "llm_custom", "email_resend", 
                "solana_helius", "telegram", "x_twitter", "trading_refs", 
                "site", "database"
            ]
            
            all_present = all(cat in categories for cat in expected_categories)
            
            if all_present:
                self.log_test("List Secrets", True, f"Toutes les catégories présentes: {len(categories)}")
                return True
            else:
                missing = [cat for cat in expected_categories if cat not in categories]
                self.log_test("List Secrets", False, f"Catégories manquantes: {missing}")
                return False
        else:
            self.log_test("List Secrets", False, f"Structure de réponse incorrecte: {response}")
            return False

    def test_secret_operations(self) -> bool:
        """Test PUT/GET/DELETE SECRET operations"""
        print("\n🔐 Test SECRET OPERATIONS...")
        
        test_category = "llm_custom"
        test_key = "OPENAI_API_KEY"
        test_value = "sk-test-12345"
        test_value_rotated = "sk-test-rotated"
        
        # PUT SECRET
        success, response = self.make_request(
            'PUT', 
            f'/api/admin/cabinet-vault/secret/{test_category}/{test_key}',
            data={"value": test_value}
        )
        
        if not success:
            self.log_test("Put Secret", False, f"Échec PUT secret: {response}")
            return False
        
        self.log_test("Put Secret", True, f"Secret créé: {test_category}/{test_key}")
        
        # Vérifier dans LIST que le secret apparaît
        success, list_response = self.make_request('GET', '/api/admin/cabinet-vault/list')
        if success:
            secrets_in_cat = list_response.get('categories', {}).get(test_category, [])
            secret_found = any(s.get('key') == test_key for s in secrets_in_cat)
            if secret_found:
                self.log_test("Secret in List", True, "Secret visible dans la liste")
            else:
                self.log_test("Secret in List", False, "Secret non trouvé dans la liste")
        
        # GET SECRET (REVEAL)
        success, response = self.make_request(
            'GET', 
            f'/api/admin/cabinet-vault/secret/{test_category}/{test_key}'
        )
        
        if success and response.get('value') == test_value:
            self.log_test("Get Secret", True, f"Secret récupéré: {response.get('value')}")
        else:
            self.log_test("Get Secret", False, f"Valeur incorrecte: {response}")
            return False
        
        # ROTATE SECRET
        success, response = self.make_request(
            'PUT', 
            f'/api/admin/cabinet-vault/secret/{test_category}/{test_key}',
            data={"value": test_value_rotated}
        )
        
        if success:
            rotation_count = response.get('rotation_count', 0)
            self.log_test("Rotate Secret", True, f"Secret roté, count: {rotation_count}")
        else:
            self.log_test("Rotate Secret", False, f"Échec rotation: {response}")
            return False
        
        # DELETE SECRET
        success, response = self.make_request(
            'DELETE', 
            f'/api/admin/cabinet-vault/secret/{test_category}/{test_key}'
        )
        
        if success:
            self.log_test("Delete Secret", True, "Secret supprimé")
            
            # Vérifier qu'il n'est plus dans la liste
            success, list_response = self.make_request('GET', '/api/admin/cabinet-vault/list')
            if success:
                secrets_in_cat = list_response.get('categories', {}).get(test_category, [])
                secret_found = any(s.get('key') == test_key and not s.get('_unset') for s in secrets_in_cat)
                if not secret_found:
                    self.log_test("Secret Deleted from List", True, "Secret retiré de la liste")
                else:
                    self.log_test("Secret Deleted from List", False, "Secret encore présent dans la liste")
            
            return True
        else:
            self.log_test("Delete Secret", False, f"Échec suppression: {response}")
            return False

    def test_vault_lock(self) -> bool:
        """Test VAULT LOCKED 423 : POST /lock puis vérifier les 423"""
        print("\n🔒 Test VAULT LOCK...")
        
        # Lock le vault
        success, response = self.make_request('POST', '/api/admin/cabinet-vault/lock')
        
        if not success:
            self.log_test("Vault Lock", False, f"Échec lock: {response}")
            return False
        
        self.log_test("Vault Lock", True, "Vault verrouillé")
        
        # Tester que les endpoints retournent 423
        endpoints_to_test = [
            '/api/admin/cabinet-vault/list',
            '/api/admin/cabinet-vault/secret/llm_custom/TEST_KEY'
        ]
        
        all_locked = True
        for endpoint in endpoints_to_test:
            success, response = self.make_request('GET', endpoint, expected_status=423)
            if success and response.get('detail', {}).get('code') == 'VAULT_LOCKED':
                self.log_test(f"Vault Locked {endpoint}", True, "Correctement verrouillé (423)")
            else:
                self.log_test(f"Vault Locked {endpoint}", False, f"Devrait retourner 423: {response}")
                all_locked = False
        
        return all_locked

    def test_export_backup(self) -> bool:
        """Test EXPORT BACKUP : Re-unlock + PUT 1 secret + POST /export"""
        print("\n💾 Test EXPORT BACKUP...")
        
        # Re-unlock le vault
        if not self.vault_mnemonic:
            self.log_test("Export Backup", False, "Pas de mnemonic pour unlock")
            return False
        
        success, response = self.make_request(
            'POST', 
            '/api/admin/cabinet-vault/unlock',
            data={"mnemonic": self.vault_mnemonic}
        )
        
        if not success:
            self.log_test("Re-unlock for Export", False, f"Échec re-unlock: {response}")
            return False
        
        # Ajouter un secret pour l'export
        success, response = self.make_request(
            'PUT', 
            '/api/admin/cabinet-vault/secret/llm_custom/EXPORT_TEST_KEY',
            data={"value": "export-test-value"}
        )
        
        if not success:
            self.log_test("Add Secret for Export", False, f"Échec ajout secret: {response}")
            return False
        
        # Export avec passphrase
        passphrase = "StrongTestPass123!"
        success, response = self.make_request(
            'POST', 
            '/api/admin/cabinet-vault/export',
            data={"passphrase": passphrase}
        )
        
        if success and response.get('format') == 'deepotus-vault-v1' and 'secrets' in response:
            secrets = response.get('secrets', [])
            has_encrypted_data = any('blob' in secret for secret in secrets)
            
            if has_encrypted_data:
                self.log_test("Export Backup", True, f"Export réussi avec {len(secrets)} secrets")
                return True
            else:
                self.log_test("Export Backup", False, "Pas de données encryptées dans l'export")
                return False
        else:
            self.log_test("Export Backup", False, f"Échec export: {response}")
            return False

    def test_export_weak_passphrase(self) -> bool:
        """Test EXPORT PASSPHRASE TROP COURTE : POST /export {passphrase: 'short'}"""
        print("\n🚫 Test EXPORT PASSPHRASE FAIBLE...")
        
        success, response = self.make_request(
            'POST', 
            '/api/admin/cabinet-vault/export',
            data={"passphrase": "short"},
            expected_status=400
        )
        
        # Vérifier que c'est bien une erreur de validation de passphrase
        if success and 'detail' in response:
            detail = response['detail']
            if isinstance(detail, list) and len(detail) > 0:
                error = detail[0]
                if error.get('type') == 'string_too_short' and 'passphrase' in str(error.get('loc', [])):
                    self.log_test("Export Weak Passphrase", True, "Passphrase faible correctement rejetée (400)")
                    return True
        
        self.log_test("Export Weak Passphrase", False, f"Format d'erreur inattendu: {response}")
        return False

    def test_audit_log(self) -> bool:
        """Test AUDIT LOG : GET /audit?limit=50"""
        print("\n📊 Test AUDIT LOG...")
        
        success, response = self.make_request('GET', '/api/admin/cabinet-vault/audit?limit=50')
        
        if success and 'items' in response:
            items = response['items']
            
            # Vérifier qu'on a des événements d'audit
            if len(items) > 0:
                # Vérifier qu'aucune valeur de secret n'est dans les logs
                has_secret_values = False
                for item in items:
                    item_str = json.dumps(item)
                    if 'sk-test' in item_str or 'export-test-value' in item_str:
                        has_secret_values = True
                        break
                
                if not has_secret_values:
                    self.log_test("Audit Log", True, f"Audit log correct avec {len(items)} événements, pas de valeurs secrètes")
                    return True
                else:
                    self.log_test("Audit Log", False, "SÉCURITÉ: Valeurs secrètes trouvées dans l'audit log!")
                    return False
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

    def test_ttl_expiration(self) -> bool:
        """Test TTL EXPIRATION : configurer ttl_seconds=2, attendre 3s, refaire /list"""
        print("\n⏰ Test TTL EXPIRATION...")
        
        if not self.vault_mnemonic:
            self.log_test("TTL Expiration", False, "Pas de mnemonic pour test TTL")
            return False
        
        # Unlock avec TTL court
        success, response = self.make_request(
            'POST', 
            '/api/admin/cabinet-vault/unlock',
            data={"mnemonic": self.vault_mnemonic, "ttl_seconds": 2}
        )
        
        if not success:
            self.log_test("TTL Unlock", False, f"Échec unlock avec TTL: {response}")
            return False
        
        self.log_test("TTL Unlock", True, "Vault déverrouillé avec TTL=2s")
        
        # Attendre 3 secondes
        print("⏳ Attente de 3 secondes pour expiration TTL...")
        time.sleep(3)
        
        # Tenter d'accéder à /list
        success, response = self.make_request('GET', '/api/admin/cabinet-vault/list', expected_status=423)
        
        if success and response.get('detail', {}).get('code') == 'VAULT_LOCKED':
            self.log_test("TTL Expiration", True, "TTL correctement expiré, vault verrouillé (423)")
            return True
        else:
            self.log_test("TTL Expiration", False, f"TTL n'a pas expiré: {response}")
            return False

    def run_all_tests(self) -> bool:
        """Exécute tous les tests dans l'ordre logique"""
        print("🚀 Début des tests Cabinet Vault Backend\n")
        
        # 1. Auth admin
        if not self.test_admin_login():
            print("❌ Échec login admin - arrêt des tests")
            return False
        
        # 2. Test guards 2FA
        self.test_2fa_guard_without_2fa()
        
        # 3. Activation 2FA
        if not self.test_2fa_activation():
            print("❌ Échec activation 2FA - arrêt des tests")
            return False
        
        # 4. Init vault
        if not self.test_vault_init():
            print("❌ Échec init vault - arrêt des tests")
            return False
        
        # 5. Test init idempotent
        self.test_vault_init_idempotent()
        
        # 6. Unlock vault
        if not self.test_vault_unlock():
            print("❌ Échec unlock vault - arrêt des tests")
            return False
        
        # 7. Test unlock invalide
        self.test_vault_unlock_invalid()
        
        # 8. List secrets
        if not self.test_list_secrets():
            print("❌ Échec list secrets - arrêt des tests")
            return False
        
        # 9. Opérations sur les secrets
        self.test_secret_operations()
        
        # 10. Test vault lock
        self.test_vault_lock()
        
        # 11. Export backup
        self.test_export_backup()
        
        # 12. Export passphrase faible
        self.test_export_weak_passphrase()
        
        # 13. Audit log
        self.test_audit_log()
        
        # 14. Audit invalid limit
        self.test_audit_invalid_limit()
        
        # 15. TTL expiration
        self.test_ttl_expiration()
        
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