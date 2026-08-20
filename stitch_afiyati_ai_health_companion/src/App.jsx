import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./state/AuthContext";
import { useLanguage } from "./state/LanguageContext";
import { LandingPage, AuthPage, ProfilePage } from "./pages/EntryPages";
import { DashboardPage, FoodHistoryPage, HistoryPage, SourcesPage, SettingsPage, HelpPage } from "./pages/DashboardPages";
import { MedicationsPage, MedicationFormPage } from "./pages/MedicationPages";
import { AskPage, FoodChatPage, MealPage, HabitsPage, SymptomsPage, EmergencyPage, TechnicalDemoPage } from "./pages/AIFlows";

function Protected({ children, allowIncomplete = false }) {
  const { user, ready } = useAuth();
  const { t } = useLanguage();
  if (!ready) return <div className="full-loader"><span className="loader-ring" /><p>{t("common.loading", "نجهز عافيتي...")}</p></div>;
  if (!user) return <Navigate to="/auth" replace />;
  if (!allowIncomplete && !user.onboarding_completed) {
    return <Navigate to="/profile?onboarding=1" replace />;
  }
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route path="/emergency" element={<EmergencyPage />} />
      <Route path="/dashboard" element={<Protected><DashboardPage /></Protected>} />
      <Route path="/profile" element={<Protected allowIncomplete><ProfilePage /></Protected>} />
      <Route path="/ask" element={<Protected><AskPage /></Protected>} />
      <Route path="/food-chat" element={<Protected><FoodChatPage /></Protected>} />
      <Route path="/meal" element={<Protected><MealPage /></Protected>} />
      <Route path="/habits" element={<Protected><HabitsPage /></Protected>} />
      <Route path="/symptoms" element={<Protected><SymptomsPage /></Protected>} />
      <Route path="/medications" element={<Protected><MedicationsPage /></Protected>} />
      <Route path="/medications/new" element={<Protected><MedicationFormPage /></Protected>} />
      <Route path="/medications/:id/edit" element={<Protected><MedicationFormPage /></Protected>} />
      <Route path="/history" element={<Protected><HistoryPage /></Protected>} />
      <Route path="/food-history" element={<Protected><FoodHistoryPage /></Protected>} />
      <Route path="/sources" element={<Protected><SourcesPage /></Protected>} />
      <Route path="/technical-demo" element={<Protected><TechnicalDemoPage /></Protected>} />
      <Route path="/settings" element={<Protected><SettingsPage /></Protected>} />
      <Route path="/help" element={<Protected><HelpPage /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
