import { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import { I18nProvider } from "@/i18n/I18nProvider";
import { ThemeProvider } from "@/theme/ThemeProvider";
import Landing from "@/pages/Landing";
import Admin from "@/pages/Admin";
import AdminEmails from "@/pages/AdminEmails";
import AdminVault from "@/pages/AdminVault";
import Operation from "@/pages/Operation";
import PublicStats from "@/pages/PublicStats";

function App() {
  useEffect(() => {
    document.title = "$DEEPOTUS — The Deep State's AI Prophet Candidate";
  }, []);

  return (
    <ThemeProvider>
      <I18nProvider>
        <div className="App min-h-screen bg-background text-foreground font-body">
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/operation" element={<Operation />} />
              <Route path="/admin" element={<Admin />} />
              <Route path="/admin/emails" element={<AdminEmails />} />
              <Route path="/admin/vault" element={<AdminVault />} />
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
