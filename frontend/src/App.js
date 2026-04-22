import { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import { I18nProvider } from "@/i18n/I18nProvider";
import { ThemeProvider } from "@/theme/ThemeProvider";
import Landing from "@/pages/Landing";
import Admin from "@/pages/Admin";

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
              <Route path="/admin" element={<Admin />} />
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
