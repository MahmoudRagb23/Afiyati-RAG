import {
  ArrowLeft,
  Bot,
  Check,
  ChevronLeft,
  ClipboardCheck,
  HeartPulse,
  Languages,
  LibraryBig,
  LockKeyhole,
  ShieldCheck,
  Siren,
  Sparkles,
  UserRoundCheck,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { api } from "../api";
import AppShell from "../components/AppShell";
import { useAuth } from "../state/AuthContext";

export function LandingPage() {
  const { user } = useAuth();
  return (
    <div className="landing">
      <header className="landing-nav">
        <Link className="brand" to="/"><span className="brand-mark">ع</span><strong>عافيتي</strong></Link>
        <nav><a href="#why">لماذا عافيتي؟</a><a href="#sources">المصادر الطبية</a></nav>
        <div className="nav-actions"><Languages size={21} /><Link className="text-link" to="/auth">دخول</Link><Link className="button small" to={user ? "/dashboard" : "/auth"}>{user ? "لوحة المتابعة" : "ابدأ الآن"}</Link></div>
      </header>
      <main>
        <section className="hero">
          <div className="hero-copy">
            <span className="eyebrow"><Sparkles size={15} /> مساعد صحي عربي قائم على الدليل</span>
            <h1>صحتك اليومية... <em>بقرارات أوضح</em></h1>
            <p>مساعد محلي للأمراض المزمنة يبحث في الإرشادات الطبية، ويربط الدليل بحالتك، ويعرض مصادره بوضوح.</p>
            <div className="hero-actions"><Link className="button" to={user ? "/dashboard" : "/auth"}>ابدأ الآن <ArrowLeft size={19} /></Link><a className="button secondary" href="#how">كيف يعمل؟</a></div>
            <Link to="/emergency" className="emergency-cta"><Siren /> طوارئ الآن</Link>
          </div>
          <div className="hero-visual" aria-label="معاينة منصة عافيتي">
            <div className="visual-glow" />
            <div className="app-preview">
              <div className="preview-top"><span className="preview-avatar">أ</span><div><strong>صباح الخير، أحمد</strong><small>ملخص عافيتك اليوم</small></div><HeartPulse /></div>
              <div className="preview-grid">
                <div className="preview-focus"><Bot /><strong>اسأل عافيتي</strong><span>حلل تأثير القهوة على حالتك</span></div>
                <div><small>قوة الدليل</small><strong>متوسط</strong><span className="mini-bar"><i /></span></div>
                <div><small>الحالات المسجلة</small><strong>حالَتان</strong><span>السكري · ضغط الدم</span></div>
              </div>
              <div className="source-pill"><ShieldCheck /><span><strong>إجابة موثقة</strong><small>3 مقاطع من إرشادات رسمية</small></span><ChevronLeft /></div>
            </div>
            <div className="floating-badge"><HeartPulse /><span><strong>سلامتك أولاً</strong><small>تصعيد الطوارئ فوري</small></span></div>
          </div>
        </section>
        <section id="why" className="why-section">
          <div className="section-center"><span className="eyebrow">ثقة قابلة للتحقق</span><h2>لماذا تثق بعافيتي؟</h2><p>نهج مصمم ليجعل حدود النظام ودليله مرئيين، لا ليحل محل الطبيب.</p></div>
          <div className="feature-grid">
            <article><span><LibraryBig /></span><h3>قائم على الأدلة</h3><p>الإجابة تأتي من ملفات الإرشادات الرسمية التي تضعها أنت في قاعدة المعرفة.</p></article>
            <article><span><UserRoundCheck /></span><h3>مخصص لحالتك</h3><p>يراعي أكثر من مرض مزمن ويبين الأثر على كل حالة بصورة منفصلة.</p></article>
            <article><span><ClipboardCheck /></span><h3>قابل للتتبع</h3><p>كل توصية مرتبطة بالوثيقة والقسم والصفحة ومعرّف المقطع المسترجع.</p></article>
          </div>
        </section>
        <section id="how" className="how-strip"><LockKeyhole /><div><h2>محلي، خاص، وقابل للقياس</h2><p>Ollama وSQLite وQdrant تعمل على جهازك دون مفاتيح مدفوعة.</p></div><Link className="button secondary" to="/technical-demo">شاهد خط الدليل</Link></section>
      </main>
      <footer id="sources"><div className="brand"><span className="brand-mark">ع</span><strong>عافيتي</strong></div><p>للتثقيف ودعم نمط الحياة فقط — لا يقدم تشخيصاً أو وصفة طبية.</p><span>© 2026 Afiyati</span></footer>
    </div>
  );
}

export function AuthPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  if (user) return <Navigate to="/dashboard" replace />;
  const submit = async (event) => {
    event.preventDefault();
    setLoading(true); setError("");
    try {
      const result = await api(`/auth/${mode === "login" ? "login" : "register"}`, {
        method: "POST",
        body: JSON.stringify(mode === "login" ? { email: form.email, password: form.password } : form),
      });
      login(result);
      navigate(mode === "login" ? "/dashboard" : "/profile");
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };
  return (
    <div className="auth-page">
      <Link to="/" className="brand auth-brand"><span className="brand-mark">ع</span><strong>عافيتي</strong></Link>
      <div className="auth-card">
        <div className="auth-intro"><span><ShieldCheck /></span><h1>{mode === "login" ? "مرحباً بعودتك" : "ابدأ رحلتك مع عافيتي"}</h1><p>بياناتك الصحية تحفظ محلياً على جهازك في هذا النموذج.</p></div>
        <div className="auth-tabs"><button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>تسجيل الدخول</button><button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>حساب جديد</button></div>
        <form onSubmit={submit} className="form-stack">
          {mode === "register" && <label>الاسم الكامل<input required minLength={2} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="مثال: أحمد محمود" /></label>}
          <label>البريد الإلكتروني<input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="name@example.com" dir="ltr" /></label>
          <label>كلمة المرور<input required minLength={8} type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="8 أحرف على الأقل" dir="ltr" /></label>
          {error && <p className="form-error">{error}</p>}
          <button className="button wide" disabled={loading}>{loading ? "جارٍ التحقق..." : mode === "login" ? "دخول آمن" : "إنشاء الحساب"}</button>
        </form>
        <div className="auth-note"><Check size={17} /> لا يتم إرسال بياناتك إلى خدمات ذكاء اصطناعي مدفوعة.</div>
      </div>
    </div>
  );
}

const conditionOptions = [
  ["hypertension", "ارتفاع ضغط الدم", HeartPulse],
  ["type_2_diabetes", "السكري من النوع الثاني", ShieldCheck],
  ["chronic_kidney_disease", "مرض الكلى المزمن", LibraryBig],
  ["asthma", "الربو", HeartPulse],
];

export function ProfilePage() {
  const { updateUser } = useAuth();
  const [form, setForm] = useState({ name: "", age: "", gender: "", height_cm: "", weight_kg: "", conditions: [], allergies: [], dietary_restrictions: [], notes: "" });
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { api("/profile").then((data) => setForm({ ...data, age: data.age || "", height_cm: data.height_cm || "", weight_kg: data.weight_kg || "", allergies: data.allergies || [], dietary_restrictions: data.dietary_restrictions || [] })).catch((err) => setError(err.message)).finally(() => setLoading(false)); }, []);
  const toggle = (condition) => setForm((current) => ({ ...current, conditions: current.conditions.includes(condition) ? current.conditions.filter((item) => item !== condition) : [...current.conditions, condition] }));
  const save = async (event) => {
    event.preventDefault(); setMessage(""); setError("");
    try {
      const result = await api("/profile", { method: "PUT", body: JSON.stringify({ ...form, age: form.age ? Number(form.age) : null, height_cm: form.height_cm ? Number(form.height_cm) : null, weight_kg: form.weight_kg ? Number(form.weight_kg) : null }) });
      setForm({ ...result, age: result.age || "", height_cm: result.height_cm || "", weight_kg: result.weight_kg || "" }); updateUser({ name: result.name }); setMessage("تم حفظ ملفك الصحي بأمان");
    } catch (err) { setError(err.message); }
  };
  return (
    <AppShell title="إعداد الملف الصحي" eyebrow="تخصيص آمن">
      {loading ? <div className="card loading-card">جارٍ تحميل ملفك...</div> : (
        <form className="profile-form card" onSubmit={save}>
          <div className="form-section"><div className="step-title"><span>1</span><div><h2>معلوماتك الأساسية</h2><p>تساعدنا على وضع الإرشادات في سياقك، ولا تستخدم للتشخيص.</p></div></div>
            <div className="form-grid"><label>الاسم<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label><label>العمر<input type="number" min="13" max="120" value={form.age} onChange={(e) => setForm({ ...form, age: e.target.value })} /></label><label>الجنس (اختياري)<select value={form.gender || ""} onChange={(e) => setForm({ ...form, gender: e.target.value || null })}><option value="">غير محدد</option><option value="male">ذكر</option><option value="female">أنثى</option></select></label><label>الطول (سم)<input type="number" value={form.height_cm} onChange={(e) => setForm({ ...form, height_cm: e.target.value })} /></label><label>الوزن (كجم)<input type="number" value={form.weight_kg} onChange={(e) => setForm({ ...form, weight_kg: e.target.value })} /></label></div>
          </div>
          <div className="form-section"><div className="step-title"><span>2</span><div><h2>الحالات المزمنة</h2><p>اختر كل الحالات التي تنطبق عليك.</p></div></div><div className="condition-picker">{conditionOptions.map(([value, label, Icon]) => <button type="button" onClick={() => toggle(value)} className={form.conditions.includes(value) ? "selected" : ""} key={value}><Icon /><span>{label}</span>{form.conditions.includes(value) && <Check />}</button>)}</div></div>
          <div className="form-section"><div className="step-title"><span>3</span><div><h2>الحساسيات والقيود الغذائية</h2><p>افصل بين العناصر بفاصلة.</p></div></div><div className="form-grid"><label>الحساسيات<input value={form.allergies.join("، ")} onChange={(e) => setForm({ ...form, allergies: e.target.value.split(/[،,]/).map((v) => v.trim()).filter(Boolean) })} placeholder="مثال: المكسرات، الحليب" /></label><label>القيود الغذائية<input value={form.dietary_restrictions.join("، ")} onChange={(e) => setForm({ ...form, dietary_restrictions: e.target.value.split(/[،,]/).map((v) => v.trim()).filter(Boolean) })} placeholder="مثال: نباتي، قليل الصوديوم" /></label></div><label>ملاحظات إضافية<textarea rows="3" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} /></label></div>
          {message && <p className="form-success">{message}</p>}{error && <p className="form-error">{error}</p>}
          <div className="form-actions"><button className="button">حفظ الملف الصحي <Check size={18} /></button><Link className="button secondary" to="/dashboard">العودة للوحة المتابعة</Link></div>
        </form>
      )}
    </AppShell>
  );
}

