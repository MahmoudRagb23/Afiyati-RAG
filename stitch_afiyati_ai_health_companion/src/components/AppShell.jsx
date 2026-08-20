import {
  Activity,
  Bell,
  Bot,
  Home,
  LibraryBig,
  LogOut,
  Menu,
  Pill,
  Salad,
  Settings,
  Siren,
  UserRound,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../state/AuthContext";
import Brand from "./Brand";
import LanguageToggle from "./LanguageToggle";
import { useLanguage } from "../state/LanguageContext";

const primary = [
  ["/dashboard", "nav.home", "الرئيسية", Home],
  ["/profile", "nav.profile", "الملف الصحي", UserRound],
  ["/ask", "nav.ask", "شات عافيتي", Bot],
  ["/meal", "nav.meal", "الطعام", Salad],
  ["/symptoms", "nav.symptoms", "الأعراض", Activity],
  ["/medications", "nav.meds", "الأدوية", Pill],
  ["/sources", "nav.sources", "المصادر", LibraryBig],
];

const titleKeys = {
  "لوحة المتابعة": "page.dashboard",
  "اسأل عافيتي": "page.ask",
  "تحليل الوجبة": "page.meal",
  "تحليل العادات": "page.habits",
  "تسجيل الأعراض": "page.symptoms",
  "إعداد الملف الصحي": "page.profile",
};

const eyebrowKeys = {
  "ملخص اليوم": "eyebrow.dashboard",
  "إجابة من الدليل، لا من الذاكرة": "eyebrow.ask",
  "اكتشاف بصري ثم تأكيد بشري": "eyebrow.meal",
  "سياقك اليومي مع الدليل": "eyebrow.habits",
  "فرز آمن دون تشخيص": "eyebrow.symptoms",
  "تخصيص آمن": "eyebrow.profile",
};

export default function AppShell({ children, title, eyebrow }) {
  const [open, setOpen] = useState(false);
  const { user, logout } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  useEffect(() => {
    const timers = [];
    if (typeof Notification !== "undefined" && Notification.permission === "granted" && user) {
      api("/medications/reminders/upcoming").then((reminders) => {
        reminders.forEach((reminder) => {
          const delay = new Date(reminder.scheduled_at).getTime() - Date.now();
          if (delay > 0 && delay <= 24 * 60 * 60 * 1000) {
            timers.push(window.setTimeout(() => {
              new Notification(`موعد ${reminder.name}`, {
                body: `${reminder.dose} — افتح عافيتي لتسجيل حالة الجرعة`,
                tag: `afiyati-dose-${reminder.medication_id}-${reminder.scheduled_at}`,
              });
            }, delay));
          }
        });
      }).catch(() => {});
    }
    return () => timers.forEach((timer) => window.clearTimeout(timer));
  }, [user]);
  const signOut = () => {
    logout();
    navigate("/");
  };
  return (
    <div className="app-layout">
      <aside className={`sidebar ${open ? "open" : ""}`} aria-label="التنقل الرئيسي">
        <div className="brand-row">
          <button className="icon-button mobile-only" onClick={() => setOpen(false)} aria-label="إغلاق القائمة">
            <X size={20} />
          </button>
          <NavLink to="/dashboard" className="brand-link"><Brand /></NavLink>
        </div>
        <div className="sidebar-welcome">
          <span className="avatar">{user?.name?.slice(0, 1) || "ع"}</span>
          <span><strong>{t("nav.welcome", "مرحباً بعودتك")}</strong><small>{t("nav.summary", "ملخص صحتك اليوم")}</small></span>
        </div>
        <nav className="side-nav">
          {primary.map(([to, labelKey, label, Icon]) => (
            <NavLink key={to} to={to} onClick={() => setOpen(false)}>
              <Icon size={20} /><span>{t(labelKey, label)}</span>
            </NavLink>
          ))}
        </nav>
        <div className="side-bottom">
          <NavLink to="/emergency" className="emergency-link"><Siren size={20} /> {t("nav.emergency", "طوارئ الآن")}</NavLink>
          <NavLink to="/settings"><Settings size={19} /> {t("nav.settings", "الإعدادات")}</NavLink>
          <LanguageToggle className="sidebar-language-toggle" />
          <button className="user-menu" onClick={signOut}>
            <span><strong>{user?.name}</strong><small>{t("nav.signOut", "تسجيل الخروج")}</small></span>
            <LogOut size={18} />
          </button>
        </div>
      </aside>
      {open && <button className="scrim" onClick={() => setOpen(false)} aria-label="إغلاق القائمة" />}
      <main className="app-main">
        <header className="app-topbar">
          <button className="icon-button" onClick={() => setOpen(true)} aria-label="فتح القائمة"><Menu /></button>
          <Brand compact />
          <div className="topbar-actions">
            <LanguageToggle />
            <NavLink to="/medications" className="icon-button notification-button" aria-label="مواعيد الأدوية"><Bell /></NavLink>
            <NavLink to="/emergency" className="mini-emergency" aria-label="الطوارئ"><Siren /></NavLink>
          </div>
        </header>
        {(title || eyebrow) && (
          <div className="page-heading">
            {eyebrow && <span className="eyebrow">{t(eyebrowKeys[eyebrow], eyebrow)}</span>}
            {title && <h1>{t(titleKeys[title], title)}</h1>}
          </div>
        )}
        <div className="page-content">{children}</div>
      </main>
      <nav className="bottom-nav" aria-label="تنقل الهاتف">
        {[primary[0], primary[2], primary[3], primary[5], primary[1]].map(([to, labelKey, label, Icon]) => (
          <NavLink key={to} to={to}><Icon size={21} /><span>{t(labelKey, label)}</span></NavLink>
        ))}
      </nav>
    </div>
  );
}
