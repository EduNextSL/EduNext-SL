import { useState } from "react";
import "./App.css";
import { LoginPage } from "./features/auth/pages/LoginPage";
import { RegisterPage } from "./features/auth/pages/RegisterPage";

function App() {
  const [view, setView] = useState<"login" | "register">("login");
  const [accountType, setAccountType] = useState<"student" | "company">(
    "student",
  );

  return (
    <main className="auth-app-shell">
      {view === "login" ? (
        <LoginPage onSwitchToRegister={() => setView("register")} />
      ) : (
        <RegisterPage
          initialAccountType={accountType}
          onAccountTypeChange={setAccountType}
          onSwitchToLogin={() => setView("login")}
        />
      )}
    </main>
  );
}

export default App;
