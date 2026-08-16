import {
  Activity,
  AlertCircle,
  Bell,
  BookOpenCheck,
  Bot,
  Camera,
  Check,
  ChevronLeft,
  CircleHelp,
  Clock3,
  Coffee,
  Database,
  ExternalLink,
  FileSearch,
  HeartPulse,
  Info,
  Pill,
  Salad,
  ShieldCheck,
  Siren,
  UserRound,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, API_URL } from "../api";
import AppShell from "../components/AppShell";

const conditionLabels = { hypertension: "ضغط الدم", type_2_diabetes: "السكري", chronic_kidney_disease: "الكلى", asthma: "الربو" };

function EmptyState({ icon: Icon = Info, title, children, action }) {
  return <div className="empty-state"><span><Icon /></span><h3>{title}</h3><p>{children}</p>{action}</div>;
}

export function DashboardPage() {
  const [data, setData] = useState({ profile: null, schedule: [], history: [] });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const load = () => Promise.all([api("/profile"), api("/medications/schedule/today"), api("/chat/history")]).then(([profile, schedule, history]) => setData({ profile, schedule, history })).catch((err) => setError(err.message)).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);
  const markDose = async (dose, status) => {
    try { await api(`/medications/${dose.medication_id}/dose`, { method: "POST", body: JSON.stringify({ scheduled_at: dose.scheduled_at, status }) }); await load(); } catch (err) { setError(err.message); }
  };
  const nextDose = data.schedule.find((item) => item.status === "upcoming");
  return (
    <AppShell>
      <div className="dashboard-heading"><div><span className="eyebrow">ملخص اليوم</span><h1>صباح الخير، {data.profile?.name || "صديق عافيتي"} <span>👋</span></h1><p>لوحة واحدة لأسئلتك، أدويتك، ومصادرك الطبية.</p></div><Link className="button emergency-button" to="/emergency"><Siren /> طوارئ</Link></div>
      {error && <div className="inline-error"><AlertCircle /> {error} <button onClick={load}>إعادة المحاولة</button></div>}
      {loading ? <div className="dashboard-skeleton"><i /><i /><i /></div> : <>
        <div className="condition-chips">{data.profile?.conditions?.length ? data.profile.conditions.map((condition) => <span key={condition}>{conditionLabels[condition] || condition}</span>) : <Link to="/profile">أضف حالاتك الصحية لتخصيص الإجابات</Link>}</div>
        <section className="dashboard-grid">
          <Link to="/ask" className="action-card primary-card"><span><Bot /></span><div><h2>اسأل عن طعام</h2><p>احصل على إجابة منفصلة لكل حالة مع الدليل.</p></div><ChevronLeft /></Link>
          <Link to="/meal" className="action-card photo-card"><Camera /><div><h2>صوّر وجبتك</h2><p>اكتشف المكونات، عدّلها، ثم حللها.</p></div><ChevronLeft /></Link>
          <Link to="/habits" className="action-card"><span className="warm"><Coffee /></span><div><h2>حلّل عادة</h2><p>القهوة والنوم والمشي والتدخين.</p></div><ChevronLeft /></Link>
          <Link to="/symptoms" className="action-card"><span className="danger-soft"><Activity /></span><div><h2>سجّل الأعراض</h2><p>فرز آمن دون تشخيص.</p></div><ChevronLeft /></Link>
        </section>
        <section className="dashboard-panels">
          <div className="card medication-widget">
            <div className="section-title"><Pill /><div><h2>جرعتك التالية</h2><p>من جدول أدويتك الحقيقي</p></div><Link to="/medications">عرض الكل</Link></div>
            {nextDose ? <div className="next-dose"><div><span className="pill-icon"><Pill /></span><div><h3>{nextDose.name} — {nextDose.dose}</h3><p><Clock3 /> {new Date(nextDose.scheduled_at).toLocaleTimeString("ar-EG", { hour: "2-digit", minute: "2-digit" })}</p></div></div><div className="dose-actions"><button className="button" onClick={() => markDose(nextDose, "taken")}><Check /> تم أخذ الجرعة</button><button className="button secondary" onClick={() => markDose(nextDose, "skipped")}>تخطي</button></div></div> : <EmptyState icon={Pill} title="لا توجد جرعة قادمة" action={<Link className="button small" to="/medications/new">أضف دواءً موصوفاً</Link>}>لن يقترح عافيتي دواءً أو جرعة من تلقاء نفسه.</EmptyState>}
          </div>
          <div className="card recent-widget">
            <div className="section-title"><Clock3 /><div><h2>آخر الأسئلة</h2><p>سجل إجاباتك الموثقة</p></div><Link to="/history">السجل</Link></div>
            {data.history.length ? <div className="recent-list">{data.history.slice(0, 3).map((item) => <Link key={item.id} to="/history"><Bot /><span><strong>{item.question}</strong><small>{new Date(`${item.created_at}Z`).toLocaleDateString("ar-EG")}</small></span><ChevronLeft /></Link>)}</div> : <EmptyState icon={Bot} title="لا توجد أسئلة بعد" action={<Link className="button small" to="/ask">اسأل عافيتي</Link>}>ستظهر إجاباتك هنا بعد أول سؤال.</EmptyState>}
          </div>
        </section>
        <section className="grounding-banner"><ShieldCheck /><div><strong>الدليل قبل الإجابة</strong><p>عندما لا تكفي المصادر المتاحة، سيقول عافيتي ذلك بوضوح بدلاً من التخمين.</p></div><Link to="/sources">افتح المصادر <ChevronLeft /></Link></section>
      </>}
    </AppShell>
  );
}

export function HistoryPage() {
  const [items, setItems] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  useEffect(() => { api("/chat/history").then(setItems).catch((err) => setError(err.message)).finally(() => setLoading(false)); }, []);
  return <AppShell title="سجل الأسئلة" eyebrow="ذاكرة قابلة للمراجعة">{error && <div className="inline-error">{error}</div>}{loading ? <div className="card loading-card">جارٍ تحميل السجل...</div> : items.length ? <div className="history-list">{items.map((item) => <article className="card" key={item.id}><div className="history-meta"><span>{item.intent || "سؤال صحي"}</span><time>{new Date(`${item.created_at}Z`).toLocaleString("ar-EG")}</time></div><h2>{item.question}</h2><p>{item.response.summary}</p><div className="history-footer"><span className={`status-chip ${item.response.recommendation_status}`}>{item.response.recommendation_status}</span><span>{item.response.citations?.length || 0} مصدر</span></div></article>)}</div> : <EmptyState icon={Bot} title="سجلك فارغ" action={<Link className="button" to="/ask">ابدأ بسؤال</Link>}>ستحفظ الإجابات هنا محلياً بعد إنشائها.</EmptyState>}</AppShell>;
}

export function SourcesPage() {
  const [sources, setSources] = useState([]); const [status, setStatus] = useState(null); const [error, setError] = useState("");
  useEffect(() => { Promise.all([api("/sources"), api("/rag/status")]).then(([sourceData, statusData]) => { setSources(sourceData); setStatus(statusData); }).catch((err) => setError(err.message)); }, []);
  return <AppShell title="المصادر الطبية" eyebrow="قاعدة معرفة محكومة">
    {error && <div className="inline-error">{error}</div>}
    <div className="status-grid"><div className="metric-card"><Database /><span>المقاطع المفهرسة</span><strong>{status?.indexed_chunks ?? "—"}</strong></div><div className="metric-card"><FileSearch /><span>مقاطع BM25</span><strong>{status?.bm25_chunks ?? "—"}</strong></div><div className="metric-card"><BookOpenCheck /><span>نموذج التضمين</span><strong className="small-value">{status?.embedding_model || "—"}</strong></div></div>
    {sources.length ? <div className="source-grid">{sources.map((source) => <article className="card source-card" key={source.guideline_id || source.title}><span className="source-org">{source.organization}</span><h2>{source.title}</h2><dl><div><dt>الحالة</dt><dd>{conditionLabels[source.condition] || source.condition}</dd></div><div><dt>الإصدار</dt><dd>{source.version || "غير مسجل"}</dd></div><div><dt>السنة</dt><dd>{source.publication_year || "غير مسجلة"}</dd></div></dl>{source.source_url && <a href={source.source_url} target="_blank" rel="noreferrer">المصدر الرسمي <ExternalLink /></a>}</article>)}</div> : <div className="card source-empty"><LibraryBig /><div><h2>قاعدة المعرفة جاهزة لاستقبال الإرشادات</h2><p>لم تتم فهرسة ملفات بعد. ضع ملفات PDF الرسمية في <code>data/guidelines</code>، حدّث <code>manifest.json</code>، ثم شغّل أداة التحقق والاستيعاب.</p><p>حتى ذلك الحين، سترفض المحادثة إعطاء توصية سريرية غير مدعومة.</p></div></div>}
  </AppShell>;
}

export function SettingsPage() {
  const [permission, setPermission] = useState(typeof Notification === "undefined" ? "unsupported" : Notification.permission);
  const enable = async () => { if (typeof Notification !== "undefined") setPermission(await Notification.requestPermission()); };
  return <AppShell title="الإعدادات" eyebrow="النموذج المحلي"><div className="settings-grid"><section className="card setting-row"><Bell /><div><h2>إشعارات الجرعات</h2><p>اسمح بإشعارات المتصفح؛ ستبقى التنبيهات داخل التطبيق متاحة دائماً.</p><small>الحالة: {permission}</small></div><button className="button secondary" onClick={enable} disabled={permission === "unsupported"}>تفعيل</button></section><section className="card setting-row"><Database /><div><h2>عنوان الخادم المحلي</h2><p>واجهة عافيتي متصلة بالخادم التالي.</p><code dir="ltr">{API_URL}</code></div></section><section className="card setting-row"><ShieldCheck /><div><h2>الخصوصية</h2><p>الحساب والملف الصحي والسجل محفوظة في SQLite محلياً. الصور لا تحفظها خدمة الاكتشاف التجريبية.</p></div></section></div></AppShell>;
}

export function HelpPage() {
  return <AppShell title="المساعدة والسلامة" eyebrow="اعرف حدود عافيتي"><div className="help-grid"><section className="card"><CircleHelp /><h2>ماذا يمكن أن يفعل؟</h2><p>شرح أثر الطعام والعادات في ضوء الإرشادات التي تمت فهرستها، مع إظهار المقاطع والمراجع.</p></section><section className="card"><AlertCircle /><h2>ماذا لا يفعل؟</h2><p>لا يشخص، لا يصف دواءً، ولا يغير جرعة أو يطلب إيقاف علاج موصوف.</p></section><section className="card emergency-help"><Siren /><h2>هل هي حالة طارئة؟</h2><p>استخدم زر الطوارئ فوراً. في مصر اتصل بالإسعاف على 123، أو استخدم رقم بلدك المحلي.</p><Link className="button emergency-button" to="/emergency">فتح وضع الطوارئ</Link></section></div></AppShell>;
}

