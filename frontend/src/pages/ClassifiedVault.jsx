/**
 * ClassifiedVault — page orchestrator.
 *
 * Composed of:
 *   - useClassifiedSession()  : session/auth/polling logic (custom hook)
 *   - <GateView />            : cinematic black-ops door + digicode
 *   - <AuthedVaultView />     : the real vault chassis once authenticated
 *
 * Page-level state lives entirely inside the hook, keeping this file
 * declarative and trivially diff-able.
 */
import { GateView } from "./classified-vault/GateView";
import { AuthedVaultView } from "./classified-vault/AuthedVaultView";
import { useClassifiedSession } from "./classified-vault/useClassifiedSession";

export default function ClassifiedVault() {
  const {
    session,
    codeInput,
    setCodeInput,
    verifying,
    gateError,
    vault,
    verifyCode,
    logout,
  } = useClassifiedSession();

  if (!session?.session_token) {
    return (
      <GateView
        codeInput={codeInput}
        setCodeInput={setCodeInput}
        verifying={verifying}
        gateError={gateError}
        verifyCode={verifyCode}
      />
    );
  }

  return (
    <AuthedVaultView session={session} vault={vault} logout={logout} />
  );
}
