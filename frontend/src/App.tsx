/**
 * App.tsx — router shell.
 *
 * Sprint 22 — migrated from .js → .tsx. The component itself takes no
 * props but we now have a fully typed router setup with explicit
 * page-component imports.
 */

import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import { I18nProvider } from "@/i18n/I18nProvider";
import { ThemeProvider } from "@/theme/ThemeProvider";
import Landing from "@/pages/Landing";
import Admin from "@/pages/Admin";
import AdminEmails from "@/pages/AdminEmails";
import AdminVault from "@/pages/AdminVault";
import AdminBots from "@/pages/AdminBots";
import CabinetVault from "@/pages/CabinetVault";
import Propaganda from "@/pages/Propaganda";
import Infiltration from "@/pages/Infiltration";
import Operation from "@/pages/Operation";
import ClassifiedVault from "@/pages/ClassifiedVault";
import PublicStats from "@/pages/PublicStats";
import HowToBuy from "@/pages/HowToBuy";
import Transparency from "@/pages/Transparency";
import Pulse from "@/pages/Pulse";
import Missions from "@/pages/Missions";
import Giveaway from "@/pages/Giveaway";

// `document.title` and SEO meta tags are synced dynamically by
// I18nProvider based on the active language (FR / EN) — see
// /src/i18n/I18nProvider.jsx.
function App(): JSX.Element {
  return (
    <ThemeProvider>
      <I18nProvider>
        <div className="App min-h-screen bg-background text-foreground font-body">
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/how-to-buy" element={<HowToBuy />} />
              <Route path="/transparency" element={<Transparency />} />
              {/* Sprint 18 — The Liquidity Pulse (omnichannel TMA landing) */}
              <Route path="/pulse" element={<Pulse />} />
              {/* Sprint 19 — Missions Hub + Giveaway */}
              <Route path="/missions" element={<Missions />} />
              <Route path="/giveaway" element={<Giveaway />} />
              <Route path="/operation" element={<Operation />} />
              <Route path="/classified-vault" element={<ClassifiedVault />} />
              <Route path="/admin" element={<Admin />} />
              <Route path="/admin/emails" element={<AdminEmails />} />
              <Route path="/admin/vault" element={<AdminVault />} />
              <Route path="/admin/bots" element={<AdminBots />} />
              <Route path="/admin/cabinet-vault" element={<CabinetVault />} />
              <Route path="/admin/propaganda" element={<Propaganda />} />
              <Route path="/admin/infiltration" element={<Infiltration />} />
              <Route path="/stats" element={<PublicStats />} />
              <Route path="*" element={<Landing />} />
            </Routes>
          </BrowserRouter>
          <Toaster
            position="bottom-right"
            toastOptions={{
              classNames: {
                toast: "font-mono text-xs",
              },
            }}
          />
        </div>
      </I18nProvider>
    </ThemeProvider>
  );
}

export default App;
