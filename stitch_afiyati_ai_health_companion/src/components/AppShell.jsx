import {
  Activity,
  Bot,
  CircleHelp,
  FlaskConical,
  History,
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

const primary = [
  ["/dashboard", "الرئيسية", Home],
  ["/ask", "اسأل عافيتي", Bot],
  ["/meal", "تحليل وجبة", Salad],
  ["/medications", "أدويتي", Pill],
  ["/symptoms", "الأعراض", Activity],
  ["/history", "السجل", History],
  ["/profile", "الملف الصحي", UserRound],
  ["/sources", "المصادر", LibraryBig],
  ["/technical-demo", "العرض التقني", FlaskConical],
];

export default function AppShell({ children, title, eyebrow }) {
  const [open, setOpen] = useState(false);
  const { user, logout } = useAuth();
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
          <NavLink to="/dashboard" className="brand">
            <span className="brand-mark">ع</span>
            <span><strong>عافيتي</strong><small>Health companion</small></span>
          </NavLink>
        </div>
        <nav className="side-nav">
          {primary.map(([to, label, Icon]) => (
            <NavLink key={to} to={to} onClick={() => setOpen(false)}>
              <Icon size={20} /><span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="side-bottom">
          <NavLink to="/emergency" className="emergency-link"><Siren size={20} /> طوارئ الآن</NavLink>
          <NavLink to="/settings"><Settings size={19} /> الإعدادات</NavLink>
          <NavLink to="/help"><CircleHelp size={19} /> المساعدة</NavLink>
          <button className="user-menu" onClick={signOut}>
            <span className="avatar">{user?.name?.slice(0, 1) || "ع"}</span>
            <span><strong>{user?.name}</strong><small>تسجيل الخروج</small></span>
            <LogOut size={18} />
          </button>
        </div>
      </aside>
      {open && <button className="scrim" onClick={() => setOpen(false)} aria-label="إغلاق القائمة" />}
      <main className="app-main">
        <header className="mobile-header">
          <button className="icon-button" onClick={() => setOpen(true)} aria-label="فتح القائمة"><Menu /></button>
          <span className="mini-brand">عافيتي</span>
          <NavLink to="/emergency" className="mini-emergency" aria-label="الطوارئ"><Siren /></NavLink>
        </header>
        {(title || eyebrow) && (
          <div className="page-heading">
            {eyebrow && <span className="eyebrow">{eyebrow}</span>}
            {title && <h1>{title}</h1>}
          </div>
        )}
        <div className="page-content">{children}</div>
      </main>
      <nav className="bottom-nav" aria-label="تنقل الهاتف">
        {[primary[0], primary[1], primary[2], primary[3], primary[6]].map(([to, label, Icon]) => (
          <NavLink key={to} to={to}><Icon size={21} /><span>{label}</span></NavLink>
        ))}
      </nav>
    </div>
  );
}
