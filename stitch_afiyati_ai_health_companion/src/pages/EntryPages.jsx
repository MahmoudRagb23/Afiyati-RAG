import {
  ArrowLeft,
  Bot,
  Check,
  ChevronLeft,
  ClipboardCheck,
  HeartPulse,
  LibraryBig,
  LockKeyhole,
  ShieldCheck,
  Siren,
  Sparkles,
  UserRoundCheck,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api";
import AppShell from "../components/AppShell";
import Brand from "../components/Brand";
import LanguageToggle from "../components/LanguageToggle";
import { SUPPORTED_CONDITION_VALUES, supportedConditions } from "../conditions";
import { useAuth } from "../state/AuthContext";
import { useLanguage } from "../state/LanguageContext";

export function LandingPage() {
  const { user } = useAuth();
  const { t } = useLanguage();
  return (
    <div className="landing">
      <header className="landing-nav">
        <Link className="brand-link" to="/"><Brand /></Link>
        <nav><a href="#why">{t("landing.why", "لماذا عافيتي؟")}</a><a href="#sources">{t("landing.sources", "المصادر الطبية")}</a></nav>
        <div className="nav-actions"><LanguageToggle /><Link className="text-link" to="/auth">{t("landing.login", "دخول")}</Link><Link className="button small" to={user ? "/dashboard" : "/auth"}>{user ? t("landing.dashboard", "لوحة المتابعة") : t("landing.start", "ابدأ الآن")}</Link></div>
      </header>
      <main>
        <section className="hero">
          <div className="hero-copy">
            <span className="eyebrow"><Sparkles size={15} /> {t("landing.eyebrow", "مساعد صحي عربي قائم على الدليل")}</span>
            <h1>{t("landing.hero", "صحتك اليومية...")} <em>{t("landing.heroAccent", "بقرارات أوضح")}</em></h1>
            <p>{t("landing.lead", "مساعد محلي للأمراض المزمنة يبحث في الإرشادات الطبية، ويربط الدليل بحالتك، ويعرض مصادره بوضوح.")}</p>
            <div className="hero-actions"><Link className="button" to={user ? "/dashboard" : "/auth"}>{t("landing.start", "ابدأ الآن")} <ArrowLeft size={19} /></Link><a className="button secondary" href="#how">{t("landing.how", "كيف يعمل؟")}</a></div>
            <Link to="/emergency" className="emergency-cta"><Siren /> {t("landing.emergency", "طوارئ الآن")}</Link>
          </div>
          <div className="hero-visual" aria-label="معاينة منصة عافيتي">
            <div className="visual-glow" />
            <div className="app-preview">
              <div className="preview-top"><span className="preview-avatar">أ</span><div><strong>{t("landing.previewGreeting", "صباح الخير، أحمد")}</strong><small>{t("landing.previewSub", "ملخص عافيتك اليوم")}</small></div><HeartPulse /></div>
              <div className="preview-grid">
                <div className="preview-focus"><Bot /><strong>{t("landing.previewAsk", "اسأل عافيتي")}</strong><span>{t("landing.previewImpact", "حلل تأثير القهوة على حالتك")}</span></div>
                <div><small>{t("landing.previewEvidence", "إجابة موثقة")}</small><strong>{t("landing.previewEvidenceValue", "جاهزة وقت الحاجة")}</strong><span className="mini-bar"><i /></span></div>
                <div><small>{t("landing.previewConditions", "الحالات المدعومة")}</small><strong>{t("landing.previewConditionValue", "السكري · ضغط الدم")}</strong></div>
              </div>
              <div className="source-pill"><ShieldCheck /><span><strong>{t("landing.previewSource", "إجابة موثقة")}</strong><small>{t("landing.previewSourceSub", "3 مقاطع من إرشادات رسمية")}</small></span><ChevronLeft /></div>
            </div>
            <div className="floating-badge"><HeartPulse /><span><strong>{t("landing.safety", "سلامتك أولاً")}</strong><small>{t("landing.safetySub", "تصعيد الطوارئ فوري")}</small></span></div>
          </div>
        </section>
        <section id="why" className="why-section">
          <div className="section-center"><span className="eyebrow">{t("landing.whyEyebrow", "ثقة قابلة للتحقق")}</span><h2>{t("landing.whyTitle", "لماذا تثق بعافيتي؟")}</h2><p>{t("landing.whyLead", "نهج مصمم ليجعل حدود النظام ودليله مرئيين، لا ليحل محل الطبيب.")}</p></div>
          <div className="feature-grid">
            <article><span><LibraryBig /></span><h3>{t("landing.featureEvidence", "قائم على الأدلة")}</h3><p>{t("landing.featureEvidenceLead", "الإجابة تأتي من ملفات الإرشادات الرسمية التي تضعها أنت في قاعدة المعرفة.")}</p></article>
            <article><span><UserRoundCheck /></span><h3>{t("landing.featurePersonal", "مخصص لحالتك")}</h3><p>{t("landing.featurePersonalLead", "يراعي ملفك الصحي ليجعل الإجابة أكثر ارتباطاً بسياقك.")}</p></article>
            <article><span><ClipboardCheck /></span><h3>{t("landing.featureTrace", "قابل للتتبع")}</h3><p>{t("landing.featureTraceLead", "كل توصية مرتبطة بالوثيقة والقسم والصفحة ومعرّف المقطع المسترجع.")}</p></article>
          </div>
        </section>
        <section id="how" className="how-strip"><LockKeyhole /><div><h2>{t("landing.private", "محلي، خاص، وقابل للقياس")}</h2><p>{t("landing.privateLead", "بياناتك تبقى على جهازك بينما يساعدك عافيتي على فهم اختياراتك اليومية.")}</p></div><Link className="button secondary" to="/technical-demo">{t("landing.openDemo", "شاهد خط الدليل")}</Link></section>
      </main>
      <footer id="sources"><Brand compact /><p>{t("landing.disclaimer", "للتثقيف ودعم نمط الحياة فقط — لا يقدم تشخيصاً أو وصفة طبية.")}</p><span>© 2026 Afiyati</span></footer>
    </div>
  );
}

export function AuthPage() {
  const { user, login } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  if (user) return <Navigate to={user.onboarding_completed ? "/dashboard" : "/profile?onboarding=1"} replace />;
  const submit = async (event) => {
    event.preventDefault();
    setLoading(true); setError("");
    try {
      const result = await api(`/auth/${mode === "login" ? "login" : "register"}`, {
        method: "POST",
        body: JSON.stringify(mode === "login" ? { email: form.email, password: form.password } : form),
      });
      login(result);
      navigate(result.user.onboarding_completed ? "/dashboard" : "/profile?onboarding=1");
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };
  return (
    <div className="auth-page">
      <Link to="/" className="brand-link auth-brand"><Brand /></Link>
      <div className="auth-card">
        <div className="auth-card-language"><LanguageToggle /></div>
        <div className="auth-intro"><span><ShieldCheck /></span><h1>{mode === "login" ? t("auth.welcome", "مرحباً بعودتك") : t("auth.join", "ابدأ رحلتك مع عافيتي")}</h1><p>{t("auth.lead", "بياناتك الصحية تحفظ محلياً على جهازك في هذا النموذج.")}</p></div>
        <div className="auth-tabs"><button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>{t("auth.login", "تسجيل الدخول")}</button><button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>{t("auth.register", "حساب جديد")}</button></div>
        <form onSubmit={submit} className="form-stack">
          {mode === "register" && <label>{t("auth.name", "الاسم الكامل")}<input required minLength={2} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder={t("auth.namePlaceholder", "مثال: أحمد محمود")} /></label>}
          <label>{t("auth.email", "البريد الإلكتروني")}<input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="name@example.com" dir="ltr" /></label>
          <label>{t("auth.password", "كلمة المرور")}<input required minLength={8} type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder={t("auth.passwordPlaceholder", "8 أحرف على الأقل")} dir="ltr" /></label>
          {error && <p className="form-error">{error}</p>}
          <button className="button wide" disabled={loading}>{loading ? t("auth.checking", "جارٍ التحقق...") : mode === "login" ? t("auth.loginAction", "دخول آمن") : t("auth.registerAction", "إنشاء الحساب")}</button>
        </form>
        <div className="auth-note"><Check size={17} /> {t("auth.note", "لا يتم إرسال بياناتك إلى خدمات ذكاء اصطناعي مدفوعة.")}</div>
      </div>
    </div>
  );
}

const conditionOptions = [
  { value: "hypertension", label: "ارتفاع ضغط الدم", Icon: HeartPulse, supported: true },
  { value: "type_2_diabetes", label: "السكري من النوع الثاني", Icon: ShieldCheck, supported: true },
  { label: "أمراض القلب والشرايين", Icon: HeartPulse, supported: false },
  { label: "مرض الكلى المزمن", Icon: LibraryBig, supported: false },
  { label: "الربو", Icon: HeartPulse, supported: false },
  { label: "ارتفاع الكوليسترول", Icon: ShieldCheck, supported: false },
  { label: "اضطرابات الغدة الدرقية", Icon: LibraryBig, supported: false },
];

const emptyProfile = {
  name: "",
  age: "",
  height_cm: "",
  weight_kg: "",
  gender: "",
  conditions: [],
  allergies: [],
  dietary_restrictions: [],
  notes: "",
};

function profileForm(data = {}) {
  return {
    ...emptyProfile,
    ...data,
    age: data.age ?? "",
    height_cm: data.height_cm ?? "",
    weight_kg: data.weight_kg ?? "",
    gender: data.gender ?? "",
    conditions: supportedConditions(data.conditions || []),
    allergies: data.allergies || [],
    dietary_restrictions: data.dietary_restrictions || [],
  };
}

export function ProfilePage() {
  const { user, updateUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isOnboarding = searchParams.get("onboarding") === "1" || !user?.onboarding_completed;
  const [form, setForm] = useState(emptyProfile);
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { api("/profile").then((data) => setForm(profileForm(data))).catch((err) => setError(err.message)).finally(() => setLoading(false)); }, []);
  const toggle = (condition) => {
    if (!SUPPORTED_CONDITION_VALUES.has(condition)) return;
    setForm((current) => ({ ...current, conditions: current.conditions.includes(condition) ? current.conditions.filter((item) => item !== condition) : [...current.conditions, condition] }));
  };
  const submit = async (event) => {
    event.preventDefault(); setMessage(""); setError("");
    if (isOnboarding && currentStep < onboardingSteps.length) {
      setCurrentStep((step) => step + 1);
      return;
    }
    setSaving(true);
    try {
      const result = await api("/profile", { method: "PUT", body: JSON.stringify({ ...form, conditions: supportedConditions(form.conditions), age: form.age ? Number(form.age) : null, height_cm: form.height_cm ? Number(form.height_cm) : null, weight_kg: form.weight_kg ? Number(form.weight_kg) : null, gender: form.gender || null }) });
      setForm(profileForm(result));
      updateUser({ name: result.name, onboarding_completed: true });
      if (isOnboarding) navigate("/dashboard", { replace: true });
      else setMessage("تم حفظ ملفك الصحي بأمان");
    } catch (err) { setError(err.message); }
    finally { setSaving(false); }
  };

  const fieldRequired = (step) => isOnboarding && currentStep === step;
  const personalSections = [
    <div className="form-section onboarding-step" key="name"><div className="step-title"><span>1</span><div><h2>ما اسمك؟</h2><p>سنستخدم الاسم الأول فقط للترحيب بك داخل عافيتي.</p></div></div><label>الاسم الكامل<input required minLength="2" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="مثال: أحمد محمود" autoComplete="name" /></label></div>,
    <div className="form-section onboarding-step" key="age"><div className="step-title"><span>2</span><div><h2>كم عمرك؟</h2><p>يساعدنا على وضع الإرشادات العامة في سياقك، ولا يستخدم للتشخيص.</p></div></div><label>العمر<input required={fieldRequired(2)} type="number" min="13" max="120" value={form.age} onChange={(event) => setForm({ ...form, age: event.target.value })} placeholder="مثال: 32" /></label></div>,
    <div className="form-section onboarding-step" key="height"><div className="step-title"><span>3</span><div><h2>ما طولك؟</h2><p>اكتب الطول بالسنتيمتر.</p></div></div><label>الطول (سم)<input required={fieldRequired(3)} type="number" min="80" max="250" value={form.height_cm} onChange={(event) => setForm({ ...form, height_cm: event.target.value })} placeholder="مثال: 175" /></label></div>,
    <div className="form-section onboarding-step" key="weight"><div className="step-title"><span>4</span><div><h2>ما وزنك؟</h2><p>اكتب الوزن بالكيلوجرام.</p></div></div><label>الوزن (كجم)<input required={fieldRequired(4)} type="number" min="20" max="400" value={form.weight_kg} onChange={(event) => setForm({ ...form, weight_kg: event.target.value })} placeholder="مثال: 70" /></label></div>,
    <div className="form-section onboarding-step" key="gender"><div className="step-title"><span>5</span><div><h2>ما جنسك؟</h2><p>هذه المعلومة اختيارية ويمكنك تركها غير محددة.</p></div></div><label>الجنس<select value={form.gender} onChange={(event) => setForm({ ...form, gender: event.target.value })}><option value="">غير محدد</option><option value="male">ذكر</option><option value="female">أنثى</option></select></label></div>,
  ];
  const conditionsSection = (
    <div className="form-section onboarding-step"><div className="step-title"><span>6</span><div><h2>الحالات المزمنة، إن وجدت</h2><p>يدعم عافيتي حالياً ارتفاع ضغط الدم والسكري فقط.</p></div></div><div className="condition-picker">{conditionOptions.map(({ value, label, Icon, supported }) => { const selected = supported && form.conditions.includes(value); return <button type="button" disabled={!supported} aria-disabled={!supported} aria-pressed={selected} onClick={() => supported && toggle(value)} className={`${selected ? "selected" : ""}${supported ? "" : " coming-soon"}`} key={value || label}><Icon /><span className="condition-option-copy"><strong>{label}</strong>{!supported && <small>Soon</small>}</span>{selected && <Check />}</button>; })}</div></div>
  );
  const allergiesSection = (
    <div className="form-section onboarding-step"><div className="step-title"><span>7</span><div><h2>الحساسيات، إن وجدت</h2><p>افصل بين العناصر بفاصلة، ويمكنك ترك الحقل فارغاً.</p></div></div><div className="form-grid"><label>الحساسيات<input value={form.allergies.join("، ")} onChange={(event) => setForm({ ...form, allergies: event.target.value.split(/[،,]/).map((value) => value.trim()).filter(Boolean) })} placeholder="مثال: المكسرات، الحليب" /></label><label>القيود الغذائية<input value={form.dietary_restrictions.join("، ")} onChange={(event) => setForm({ ...form, dietary_restrictions: event.target.value.split(/[،,]/).map((value) => value.trim()).filter(Boolean) })} placeholder="مثال: نباتي، قليل الصوديوم" /></label></div><label>ملاحظات إضافية<textarea rows="3" value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} placeholder="معلومة تساعدك على تذكر ما تريد مناقشته مع الطبيب" /></label></div>
  );
  const onboardingSteps = ["الاسم", "العمر", "الطول", "الوزن", "الجنس", "الحالات المزمنة", "الحساسيات"];
  const activeOnboardingSection = currentStep <= 5 ? personalSections[currentStep - 1] : currentStep === 6 ? conditionsSection : allergiesSection;
  return (
    <AppShell title="إعداد الملف الصحي" eyebrow="تخصيص آمن">
      {loading ? <div className="card loading-card">جارٍ تحميل ملفك...</div> : (
        <form className={`profile-form card${isOnboarding ? " onboarding-card" : ""}`} onSubmit={submit}>
          {isOnboarding && <div className="profile-progress"><div><strong>الخطوة {currentStep} من {onboardingSteps.length}</strong><span>{onboardingSteps[currentStep - 1]}</span></div><div className="profile-progress-track" style={{ "--progress-steps": onboardingSteps.length }}>{onboardingSteps.map((step, index) => <i aria-label={step} className={index + 1 <= currentStep ? "active" : ""} key={step} />)}</div></div>}
          {isOnboarding ? activeOnboardingSection : <>{personalSections}{conditionsSection}{allergiesSection}</>}
          {message && <p className="form-success">{message}</p>}{error && <p className="form-error">{error}</p>}
          {isOnboarding ? <div className="form-actions onboarding-actions">{currentStep > 1 && <button type="button" className="button secondary" onClick={() => setCurrentStep((step) => step - 1)}>السابق</button>}<button className="button" disabled={saving}>{saving ? "جارٍ الحفظ..." : currentStep < onboardingSteps.length ? "التالي" : "إكمال إنشاء الحساب"} {currentStep === onboardingSteps.length ? <Check size={18} /> : <ChevronLeft size={18} />}</button></div> : <div className="form-actions"><button className="button" disabled={saving}>{saving ? "جارٍ الحفظ..." : "حفظ الملف الصحي"} <Check size={18} /></button><Link className="button secondary" to="/dashboard">العودة للوحة المتابعة</Link></div>}
        </form>
      )}
    </AppShell>
  );
}
