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
  LibraryBig,
  Pill,
  Salad,
  ShieldCheck,
  Siren,
  Scale,
  UserRound,
  UtensilsCrossed,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, API_URL } from "../api";
import AppShell from "../components/AppShell";

const conditionLabels = { hypertension: "ضغط الدم", type_2_diabetes: "السكري" };
const foodSourceTypeLabels = {
  nutrition_database: "قاعدة تركيب غذائي رسمية",
  quality_framework_and_catalogue: "مرجع جودة وفهرس قواعد عالمية",
};

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
        <section className="front-bento-grid">
          <Link to="/ask" className="front-bento-card featured"><span><Bot /></span><div><h2>شات عافيتي</h2><p>تحدث مع مساعدك الصحي واحصل على إجابات مرتبطة بالمصادر.</p></div><ChevronLeft /></Link>
          <Link to="/food-chat" className="front-bento-card food"><span><UtensilsCrossed /></span><div><h2>شات الأكل</h2><p>اسأل عن الطعام والمشروبات والكميات.</p></div><ChevronLeft /></Link>
          <Link to="/symptoms" className="front-bento-card symptoms"><span><Activity /></span><div><h2>متابعة الأعراض</h2><p>سجّل كيف تشعر اليوم بأمان.</p></div><ChevronLeft /></Link>
          <Link to="/meal" className="front-bento-card meal"><span><Camera /></span><div><h2>تحليل وجبة</h2><p>صوّر وجبتك وراجع المكونات قبل التحليل.</p></div><ChevronLeft /></Link>
          <Link to="/food-history" className="front-bento-card history"><span><BookOpenCheck /></span><div><h2>سجل الطعام</h2><p>راجع وجباتك والقيم المسجلة سابقاً.</p></div><ChevronLeft /></Link>
          <Link to="/medications" className="front-bento-card medications"><span><Pill /></span><div><h2>الأدوية</h2><p>تابع المواعيد وسجّل حالة الجرعة.</p></div><ChevronLeft /></Link>
          <Link to="/sources" className="front-bento-card sources"><span><LibraryBig /></span><div><h2>المصادر</h2><p>راجع قواعد البيانات والإرشادات المستخدمة.</p></div><ChevronLeft /></Link>
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

const foodNutrientLabels = {
  calories_kcal: "السعرات",
  carbohydrates_g: "الكربوهيدرات",
  sugars_g: "السكريات",
  protein_g: "البروتين",
  fat_g: "الدهون",
  sodium_mg: "الصوديوم",
  caffeine_mg: "الكافيين",
};

const foodUnitLabels = { KCAL: "سعر", kcal: "سعر", G: "جم", g: "جم", MG: "مجم", mg: "مجم" };

export function FoodHistoryPage() {
  const [items, setItems] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  useEffect(() => { api("/foods/history").then(setItems).catch((err) => setError(err.message)).finally(() => setLoading(false)); }, []);
  return <AppShell title="سجل الطعام" eyebrow="الكميات والقيم من المصدر">
    <div className="page-toolbar"><p>كل طعام أو مشروب تم تحليله، بالكمية التي أدخلتها والمصدر المستخدم.</p><Link className="button" to="/meal"><Salad /> تحليل وجبة جديدة</Link></div>
    {error && <div className="inline-error">{error}</div>}
    {loading ? <div className="card loading-card">جارٍ تحميل سجل الطعام...</div> : items.length ? <div className="food-history-list">{items.map((record) => <article className="card food-history-card" key={record.id}><div className="history-meta"><span>{record.mode === "meal" ? "وجبة" : "طعام أو مشروب"}</span><time>{new Date(`${record.created_at}Z`).toLocaleString("ar-EG")}</time></div><h2>{record.question}</h2><div className="food-history-items">{record.items.map((food) => <div className="food-history-item" key={`${record.id}-${food.source.record_id}-${food.requested_name}`}><div className="food-history-heading"><UtensilsCrossed /><div><strong>{food.requested_name}</strong><small>{food.matched_name}</small></div><span><Scale /> {food.amount_g || 100} جم</span></div><div className="food-history-nutrients">{Object.entries(food.nutrients || {}).filter(([key]) => foodNutrientLabels[key]).slice(0, 7).map(([key, nutrient]) => <div key={key}><span>{foodNutrientLabels[key]}</span><strong>{nutrient.value} {foodUnitLabels[nutrient.unit] || nutrient.unit}</strong></div>)}</div><a href={food.source.url} target="_blank" rel="noreferrer">{food.source.title} · FDC {food.source.record_id} <ExternalLink /></a></div>)}</div></article>)}</div> : <EmptyState icon={UtensilsCrossed} title="سجل الطعام فارغ" action={<Link className="button" to="/ask">اسأل عن طعام</Link>}>أي تحليل يحتوي طعاماً موثقاً سيُحفظ هنا تلقائياً مع الكمية والمصدر.</EmptyState>}
  </AppShell>;
}

export function SourcesPage() {
  const [sources, setSources] = useState([]); const [foodData, setFoodData] = useState({ sources: [], status: null, health_rules: {} }); const [status, setStatus] = useState(null); const [error, setError] = useState("");
  useEffect(() => { Promise.all([api("/sources"), api("/rag/status"), api("/foods/sources")]).then(([sourceData, statusData, foodSourceData]) => { setSources(sourceData); setStatus(statusData); setFoodData(foodSourceData); }).catch((err) => setError(err.message)); }, []);
  const officialFoodDatabases = foodData.sources.filter((source) => source.type === "nutrition_database" && source.active).length;
  return <AppShell title="المصادر" eyebrow="شفافية كاملة: من أين جاءت كل معلومة؟">
    {error && <div className="inline-error">{error}</div>}
    <div className="status-grid"><div className="metric-card"><Database /><span>قواعد الغذاء الرسمية</span><strong>{officialFoodDatabases || "—"}</strong></div><div className="metric-card"><FileSearch /><span>المقاطع الطبية المفهرسة</span><strong>{status?.indexed_chunks ?? "—"}</strong></div><div className="metric-card"><BookOpenCheck /><span>أسماء الطعام المدعومة</span><strong>{foodData.status?.aliases ?? "—"}</strong></div></div>
    <section className="source-section">
      <div className="source-section-heading"><Database /><div><h2>مصادر بيانات الطعام والمشروبات</h2><p>تُعرض أرقام كل مصدر مستقلة. لا يدمج عافيتي القيم ولا يأخذ متوسطها.</p></div></div>
      <div className="source-grid">{foodData.sources.map((source) => <article className="card source-card food-database-card" key={source.id}><div className="source-card-badges"><span className="source-org">{source.organization}</span><span className={source.active ? "active-source" : "reference-source"}>{source.active ? "نشط" : "مرجعي"}</span></div><h2>{source.name}</h2><p>{source.usage}</p><dl><div><dt>الدور</dt><dd>{foodSourceTypeLabels[source.type] || source.type}</dd></div><div><dt>الإصدار</dt><dd>{source.version || "محدّث باستمرار"}</dd></div><div><dt>الترخيص</dt><dd>{source.license || "راجع المصدر"}</dd></div></dl>{source.website_url && <a href={source.website_url} target="_blank" rel="noreferrer">الموقع الرسمي <ExternalLink /></a>}</article>)}</div>
    </section>
    {!!foodData.health_rules?.medical_sources?.length && <section className="source-section">
      <div className="source-section-heading"><ShieldCheck /><div><h2>مصادر قواعد الطعام حسب الحالة</h2><p>تحدد بطاقات «قلّل» و«راجع الكمية» و«لا ضرر خاص موثق» من هذه المراجع، وليس من تخمين النموذج.</p></div></div>
      <div className="source-grid">{foodData.health_rules.medical_sources.map((source) => <article className="card source-card" key={source.id}><span className="source-org">{source.organization}</span><h2>{source.title}</h2><p>{source.use}</p><dl><div><dt>القسم</dt><dd>{source.section}</dd></div></dl><a href={source.url} target="_blank" rel="noreferrer">افتح المصدر الطبي <ExternalLink /></a></article>)}</div>
    </section>}
    {!!foodData.health_rules?.activities?.length && <section className="source-section">
      <div className="source-section-heading"><BookOpenCheck /><div><h2>دليل الأنشطة والرياضات</h2><p>الأنشطة مفصولة في ملف بيانات مستقل مع مصادرها؛ لا تُعرض كبديل للعلاج أو لتقييم الطبيب.</p></div></div>
      <div className="source-grid">{foodData.health_rules.activities.map((activity) => <article className="card source-card" key={activity.id}><span className="source-org">{activity.category}</span><h2>{activity.name_ar}</h2><p>{activity.summary}</p><dl><div><dt>المراجع</dt><dd>{activity.source_ids?.length || 0} مصادر</dd></div></dl></article>)}</div>
    </section>}
    <section className="source-section">
      <div className="source-section-heading"><ShieldCheck /><div><h2>مصادر التقييم الصحي</h2><p>لا تستخدم الإجابة الطبية إلا المقاطع المفهرسة التي تظهر كمراجع مباشرة.</p></div></div>
      {sources.length ? <div className="source-grid">{sources.map((source) => <article className="card source-card" key={source.guideline_id || source.title}><span className="source-org">{source.organization}</span><h2>{source.title}</h2><dl><div><dt>الحالة</dt><dd>{conditionLabels[source.condition] || source.condition}</dd></div><div><dt>الإصدار</dt><dd>{source.version || "غير مسجل"}</dd></div><div><dt>السنة</dt><dd>{source.publication_year || "غير مسجلة"}</dd></div></dl>{source.source_url && <a href={source.source_url} target="_blank" rel="noreferrer">المصدر الرسمي <ExternalLink /></a>}</article>)}</div> : <div className="card source-empty"><LibraryBig /><div><h2>لا توجد إرشادات طبية مفهرسة</h2><p>حتى تتوفر إرشادات موثقة، سترفض المحادثة إعطاء توصية سريرية غير مدعومة.</p></div></div>}
    </section>
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
