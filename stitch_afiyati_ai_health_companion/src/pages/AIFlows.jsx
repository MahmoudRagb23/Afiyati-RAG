import {
  Activity,
  AlertOctagon,
  AlertTriangle,
  ArrowLeft,
  BedDouble,
  Bot,
  BrainCircuit,
  Camera,
  Check,
  CheckCircle2,
  ChevronLeft,
  CigaretteOff,
  CircleGauge,
  ClipboardCheck,
  Clock3,
  Coffee,
  Database,
  Dumbbell,
  Edit3,
  FileCheck2,
  FlaskConical,
  Footprints,
  ImagePlus,
  LoaderCircle,
  MessageCircleQuestion,
  PhoneCall,
  Plus,
  Search,
  Send,
  ShieldAlert,
  ShieldCheck,
  Siren,
  Sparkles,
  Trash2,
  Utensils,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { api } from "../api";
import AnswerView from "../components/AnswerView";
import AppShell from "../components/AppShell";
import { isEmergencyMessage, isSymptomCheckIn } from "../safety";
import { useAuth } from "../state/AuthContext";
import { useLanguage } from "../state/LanguageContext";

const loadingStages = ["أحدد الطعام أو المشروب...", "أتحقق من USDA وCoFID...", "أبحث في الإرشادات الطبية...", "أجهز الإجابة ومصادرها..."];
const loadingStageKeys = ["loader.food", "loader.sources", "loader.guidance", "loader.answer"];
const chatConditionLabels = { hypertension: "ارتفاع ضغط الدم", type_2_diabetes: "السكري من النوع الثاني" };

function StagedLoader({ stage }) {
  const { isEnglish, t } = useLanguage();
  const englishStages = ["Finding the food or drink...", "Checking official food data...", "Retrieving medical guidance...", "Preparing your sourced answer..."];
  return <div className="staged-loader"><div className="scan-orbit"><Search /><i /></div><div><strong>{t(loadingStageKeys[stage], isEnglish ? englishStages[stage] : loadingStages[stage])}</strong><span>{isEnglish ? `${stage + 1} of ${loadingStages.length}` : `${stage + 1} من ${loadingStages.length}`}</span><div className="stage-progress"><i style={{ width: `${((stage + 1) / loadingStages.length) * 100}%` }} /></div></div></div>;
}

function useGroundedQuestion() {
  const [answer, setAnswer] = useState(null); const [loading, setLoading] = useState(false); const [stage, setStage] = useState(0); const [error, setError] = useState("");
  const ask = async (payload) => {
    setLoading(true); setAnswer(null); setError(""); setStage(0);
    const interval = window.setInterval(() => setStage((current) => Math.min(current + 1, loadingStages.length - 1)), 1800);
    try { const result = await api("/chat", { method: "POST", body: JSON.stringify(payload) }); setAnswer(result); if (result.trace_id) sessionStorage.setItem("afiyati_trace_id", result.trace_id); return result; }
    catch (err) { setError(err.message); return null; }
    finally { window.clearInterval(interval); setLoading(false); }
  };
  return { answer, loading, stage, error, ask, setAnswer };
}

const chatModes = [
  { id: "general", Icon: Bot, ar: "شات عافيتي", en: "Afiyati chat", descriptionAr: "اسأل أو كمل محادثة سابقة", descriptionEn: "Ask or continue a conversation" },
  { id: "food", Icon: Utensils, ar: "شات الأكل", en: "Food chat", descriptionAr: "طعام، مشروبات، وكميات", descriptionEn: "Food, drinks, and amounts" },
  { id: "symptom", Icon: Activity, ar: "متابعة الأعراض", en: "Symptom follow-up", descriptionAr: "سجّل ما تشعر به بأمان", descriptionEn: "Record how you feel safely" },
];

function SymptomFollowUp({ result, history, isEnglish }) {
  const labels = {
    monitoring: isEnglish ? "Monitor and record" : "مراقبة وتسجيل",
    professional_evaluation_recommended: isEnglish ? "Professional review recommended" : "ينصح بتقييم مهني",
  };
  return <section className="symptom-chat-follow-up">
    {result && <div className={`symptom-result ${result.classification || "monitoring"}`}><Activity /><div><strong>{labels[result.classification] || (isEnglish ? "Symptom update" : "تحديث الأعراض")}</strong><p>{result.message}</p></div></div>}
    <div className="symptom-history-heading"><div><Clock3 /><span><strong>{isEnglish ? "Recent symptom check-ins" : "آخر متابعات الأعراض"}</strong><small>{isEnglish ? "Saved privately to help you notice changes." : "محفوظة محلياً لتلاحظ التغيّر مع الوقت."}</small></span></div><Link to="/symptoms">{isEnglish ? "Full tracker" : "المتابعة الكاملة"} <ChevronLeft /></Link></div>
    {history.length ? <div className="symptom-history-list">{history.slice(0, 4).map((item) => <article key={item.id}><span className={`symptom-severity severity-${item.severity}`}>{isEnglish ? `Level ${item.severity}/10` : `الشدة ${item.severity}/10`}</span><div><strong>{item.symptoms}</strong><small>{new Date(`${item.created_at}Z`).toLocaleString(isEnglish ? "en-GB" : "ar-EG", { dateStyle: "medium", timeStyle: "short" })}</small></div></article>)}</div> : <p className="symptom-history-empty">{isEnglish ? "Your check-ins will appear here after the first update." : "ستظهر متابعاتك هنا بعد أول تسجيل."}</p>}
  </section>;
}

export function AskPage({ defaultMode = "general" }) {
  const [question, setQuestion] = useState(""); const [profile, setProfile] = useState(null); const [activeMode, setActiveMode] = useState(defaultMode); const [foodAmount, setFoodAmount] = useState(""); const [symptomSeverity, setSymptomSeverity] = useState(4); const [symptomHistory, setSymptomHistory] = useState([]); const [symptomResult, setSymptomResult] = useState(null); const [symptomLoading, setSymptomLoading] = useState(false); const [symptomError, setSymptomError] = useState(""); const { user } = useAuth(); const navigate = useNavigate(); const inputRef = useRef(null); const { answer, loading, stage, error, ask, setAnswer } = useGroundedQuestion();
  const { isEnglish, t } = useLanguage();
  const loadSymptomHistory = () => api("/symptoms/history").then(setSymptomHistory).catch(() => setSymptomHistory([]));
  useEffect(() => { api("/profile").then(setProfile).catch(() => setProfile(null)); loadSymptomHistory(); }, []);
  const selectedMode = chatModes.find((mode) => mode.id === activeMode) || chatModes[0];
  const examples = {
    general: isEnglish ? ["Can walking help my blood pressure?", "What about coffee with my profile?", "Show me the sources from the last answer."] : ["هل المشي مفيد لضغط الدم؟", "ماذا عن القهوة مع حالتي؟", "ما مصادر الإجابة السابقة؟"],
    food: isEnglish ? ["200 g banana", "A cup of black coffee", "150 g low-fat milk"] : ["200 جم موز", "كوب قهوة سوداء", "150 جم حليب قليل الدسم"],
    symptom: isEnglish ? ["I have had a headache since this morning", "I feel dizzy after lunch", "My heart is racing"] : ["عندي صداع منذ الصباح", "أشعر بدوخة بعد الغداء", "أشعر بخفقان في القلب"],
  }[activeMode];
  const placeholder = activeMode === "food"
    ? (isEnglish ? "For example: black coffee or 200 g banana" : "مثال: قهوة سوداء أو 200 جم موز")
    : activeMode === "symptom"
      ? (isEnglish ? "Describe what you feel and when it started" : "اكتب ما تشعر به ومتى بدأ")
      : t("ask.placeholder", "مثال: أنا عندي ضغط وسكري، هل القهوة مناسبة؟");
  const firstName = (profile?.name || user?.name || "صديق عافيتي").trim().split(" ")[0];
  const goToEmergency = () => navigate("/emergency", { state: { triggered: true } });
  const changeMode = (mode) => { setActiveMode(mode); setAnswer(null); setSymptomResult(null); setSymptomError(""); };
  const saveSymptomCheckIn = async (cleanQuestion, automatic = false) => {
    setSymptomLoading(true); setSymptomError(""); setSymptomResult(null);
    if (automatic) { setActiveMode("symptom"); setAnswer(null); }
    try {
      const result = await api("/symptoms", { method: "POST", body: JSON.stringify({ symptoms: cleanQuestion, severity: Number(symptomSeverity), context: automatic ? "تم التوجيه تلقائياً من شات عافيتي" : "تم التسجيل من شات متابعة الأعراض" }) });
      if (result.emergency) { goToEmergency(); return; }
      setSymptomResult(result); setQuestion(""); await loadSymptomHistory();
    } catch (err) { setSymptomError(err.message); }
    finally { setSymptomLoading(false); }
  };
  const submit = async (event) => {
    event.preventDefault();
    const cleanQuestion = question.trim();
    if (!cleanQuestion) return;
    if (isEmergencyMessage(cleanQuestion)) { goToEmergency(); return; }
    if (activeMode === "symptom" || (activeMode === "general" && isSymptomCheckIn(cleanQuestion))) {
      await saveSymptomCheckIn(cleanQuestion, activeMode === "general");
      return;
    }
    const payload = { question: cleanQuestion, mode: activeMode === "food" ? "food" : "chat" };
    if (activeMode === "food" && foodAmount) payload.food_quantities = [{ name: cleanQuestion, amount_g: Number(foodAmount) }];
    const result = await ask(payload);
    if (result?.emergency) { goToEmergency(); return; }
  };
  const pageTitle = activeMode === "food" ? (isEnglish ? "Food chat" : "شات الأكل") : activeMode === "symptom" ? (isEnglish ? "Symptom follow-up" : "متابعة الأعراض") : "اسأل عافيتي";
  return <AppShell title={pageTitle} eyebrow="إجابة من الدليل، لا من الذاكرة">
    <div className="ask-layout">
      <section className="ask-main card"><div className="assistant-intro"><span>{activeMode === "symptom" ? <Activity /> : activeMode === "food" ? <Utensils /> : <Bot />}</span><div><h2>{t("ask.greeting", "أهلاً يا")} {firstName} <span className="wave">👋</span></h2><p>{activeMode === "symptom" ? (isEnglish ? "I will help you record changes safely and escalate emergencies immediately." : "سأساعدك على تسجيل التغيّرات بأمان، وأحوّل الطوارئ فوراً.") : activeMode === "food" ? (isEnglish ? "Ask about food or drinks and see their data and sources separately." : "اسأل عن أي طعام أو مشروب وشاهد بياناته ومصادره بشكل منفصل.") : t("ask.intro", "أنا أراعي ملفك الصحي المسجل وسياق آخر محادثاتك، لكن كل توصية تظل مرتبطة بدليل ظاهر.")}</p></div></div>
        <div className="chat-mode-tabs" role="tablist" aria-label={isEnglish ? "Conversation type" : "نوع المحادثة"}>{chatModes.map(({ id, Icon, ar, en, descriptionAr, descriptionEn }) => <button type="button" role="tab" aria-selected={activeMode === id} className={activeMode === id ? "active" : ""} onClick={() => changeMode(id)} key={id}><Icon /><span><strong>{isEnglish ? en : ar}</strong><small>{isEnglish ? descriptionEn : descriptionAr}</small></span></button>)}</div>
        {activeMode !== "symptom" && <div className="profile-context-strip"><div><ShieldCheck /><span><strong>{t("ask.context", "السياق المستخدم")}</strong><small>{t("ask.contextLead", "بياناتك المبلّغ عنها للتخصيص وليست دليلاً طبياً")}</small></span></div><div className="profile-context-chips">{profile?.conditions?.map((condition) => <span key={condition}>{isEnglish ? ({ hypertension: "High blood pressure", type_2_diabetes: "Type 2 diabetes" }[condition] || condition) : (chatConditionLabels[condition] || condition)}</span>)}{profile?.allergies?.slice(0, 3).map((allergy) => <span className="allergy" key={allergy}>{isEnglish ? "Allergy" : "حساسية"}: {allergy}</span>)}{!profile?.conditions?.length && !profile?.allergies?.length && <span>{t("ask.emptyContext", "لا توجد حالات أو حساسيات مسجلة")}</span>}<Link to="/profile">{t("ask.edit", "تعديل الملف")}</Link></div></div>}
        {!answer && !loading && activeMode !== "symptom" && <div className="prompt-examples">{examples.map((example) => <button key={example} onClick={() => { setQuestion(example); inputRef.current?.focus(); }}><MessageCircleQuestion />{example}<ChevronLeft /></button>)}</div>}
        {activeMode === "symptom" && <div className="symptom-chat-intro"><ShieldAlert /><div><strong>{isEnglish ? "For urgent symptoms, we switch to emergency mode immediately." : "في الأعراض الطارئة سنحوّلك لوضع الطوارئ فوراً."}</strong><p>{isEnglish ? "For other symptoms, tell us the change and choose its current severity." : "أما غير الطارئة، اكتب ما تغيّر وحدد شدته الحالية."}</p></div></div>}
        {activeMode === "symptom" && <div className="symptom-severity-control"><span>{isEnglish ? "Current severity" : "الشدة الحالية"}</span><strong>{symptomSeverity}/10</strong><input type="range" min="1" max="10" value={symptomSeverity} onChange={(event) => setSymptomSeverity(event.target.value)} /></div>}
        {activeMode === "food" && <label className="food-chat-amount">{isEnglish ? "Amount in grams (optional)" : "الكمية بالجرام (اختياري)"}<input type="number" min="1" max="5000" value={foodAmount} onChange={(event) => setFoodAmount(event.target.value)} placeholder={isEnglish ? "e.g. 200" : "مثال: 200"} dir="ltr" /></label>}
        {activeMode === "symptom" && <div className="prompt-examples">{examples.map((example) => <button key={example} onClick={() => { setQuestion(example); inputRef.current?.focus(); }}><Activity />{example}<ChevronLeft /></button>)}</div>}
        {loading && <StagedLoader stage={stage} />}{error && activeMode !== "symptom" && <div className="inline-error"><AlertTriangle />{error}</div>}{symptomError && <div className="inline-error"><AlertTriangle />{symptomError}</div>}
        {activeMode !== "symptom" && <AnswerView answer={answer} onTechnical={(traceId) => { sessionStorage.setItem("afiyati_trace_id", traceId); navigate("/technical-demo"); }} />}
        {activeMode === "symptom" && <SymptomFollowUp result={symptomResult} history={symptomHistory} isEnglish={isEnglish} />}
        <form className="chat-composer" onSubmit={submit}><textarea ref={inputRef} rows="2" maxLength="2000" required value={question} onChange={(e) => setQuestion(e.target.value)} placeholder={placeholder} /><button className="send-button" disabled={loading || symptomLoading || !question.trim()} aria-label={isEnglish ? "Send question" : "إرسال السؤال"}>{loading || symptomLoading ? <LoaderCircle className="spin" /> : <Send />}</button></form>
        <p className="composer-note"><ShieldCheck /> {activeMode === "symptom" ? (isEnglish ? "This does not diagnose. Chest pain, choking, loss of consciousness, severe bleeding, or sudden weakness go to emergency immediately." : "هذه متابعة وليست تشخيصاً. ألم الصدر أو الاختناق أو فقدان الوعي أو النزيف الشديد أو الضعف المفاجئ يحوّل للطوارئ فوراً.") : activeMode === "food" ? (isEnglish ? "Add grams for food values linked to a specific amount and their official source." : "أضف الكمية بالجرام للحصول على قيم مرتبطة بكمية محددة ومصدرها الرسمي.") : t("ask.note", "لحساب دقيق اكتب الكمية بالجرام، مثل: 200 جم موز.")}</p>
      </section>
      <aside className="ask-aside"><div className="card"><h3>{activeMode === "symptom" ? (isEnglish ? "How follow-up works" : "كيف تعمل المتابعة؟") : activeMode === "food" ? (isEnglish ? "Food chat, clearly" : "شات الأكل بوضوح") : t("ask.how", "كيف تُبنى الإجابة؟")}</h3><ol>{activeMode === "symptom" ? <><li><span>1</span>{isEnglish ? "You describe the symptom and its severity." : "تكتب العرض وتحدد شدته."}</li><li><span>2</span>{isEnglish ? "Emergency signs bypass chat immediately." : "العلامات الطارئة تتجاوز المحادثة فوراً."}</li><li><span>3</span>{isEnglish ? "Other updates are saved privately for follow-up." : "أما غير الطارئة فتُحفظ محلياً للمتابعة."}</li></> : activeMode === "food" ? <><li><span>1</span>{isEnglish ? "Name the food or drink." : "سمِّ الطعام أو المشروب."}</li><li><span>2</span>{isEnglish ? "Add grams if you know the amount." : "أضف الجرامات إن عرفت الكمية."}</li><li><span>3</span>{isEnglish ? "See official data and health sources separately." : "شاهد البيانات الرسمية والمصادر الطبية كلٌ على حدة."}</li></> : <><li><span>1</span>{t("ask.step1", "فهم سؤالك وسياقك المسجل")}</li><li><span>2</span>{t("ask.step2", "USDA مع تحقق CoFID عند توفر تطابق")}</li><li><span>3</span>{t("ask.step3", "إرشادات تناسب حالتك")}</li><li><span>4</span>{t("ask.step4", "روابط السجلات والمراجع المباشرة")}</li></>}</ol>{activeMode !== "symptom" && <Link className="source-transparency-link" to="/sources">{t("ask.sources", "شاهد سياسة ومصادر البيانات")} <ChevronLeft /></Link>}</div><div className="safety-mini"><ShieldAlert /><p>{t("ask.safety", "لا تستخدم المحادثة في الطوارئ.")}</p><Link to="/emergency">{t("ask.emergency", "افتح وضع الطوارئ")}</Link></div></aside>
    </div>
  </AppShell>;
}

export function FoodChatPage() {
  return <AskPage defaultMode="food" />;
}

export function MealPage() {
  const [file, setFile] = useState(null); const [preview, setPreview] = useState(""); const [ingredients, setIngredients] = useState([]); const [draft, setDraft] = useState(""); const [detecting, setDetecting] = useState(false); const [notice, setNotice] = useState(""); const navigate = useNavigate(); const { answer, loading, stage, error, ask } = useGroundedQuestion();
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);
  const choose = (selected) => { if (!selected) return; if (preview) URL.revokeObjectURL(preview); setFile(selected); setPreview(URL.createObjectURL(selected)); setIngredients([]); setNotice(""); };
  const detect = async () => { if (!file) return; setDetecting(true); const body = new FormData(); body.append("file", file); try { const result = await api("/meals/detect", { method: "POST", body }); setIngredients(result.ingredients.map((name) => ({ name, amount_g: 100 }))); setNotice(result.notice); } catch (err) { setNotice(err.message); } finally { setDetecting(false); } };
  const addIngredient = () => { if (draft.trim()) { setIngredients([...ingredients, { name: draft.trim(), amount_g: 100 }]); setDraft(""); } };
  const analyze = async () => { const result = await ask({ question: "حلل هذه الوجبة في ضوء حالاتي الصحية المسجلة.", confirmed_ingredients: ingredients.map((item) => item.name), food_quantities: ingredients, mode: "meal" }); if (result?.emergency) navigate("/emergency", { state: { triggered: true } }); };
  return <AppShell title="تحليل الوجبة" eyebrow="اكتشاف بصري ثم تأكيد بشري">
    <div className="meal-grid"><section className="card upload-card"><div className="section-title"><Camera /><div><h2>صورة الوجبة</h2><p>الصورة تستخدم لاكتشاف مكونات محتملة فقط</p></div></div><label className={`drop-zone ${preview ? "has-image" : ""}`}>{preview ? <img src={preview} alt="معاينة الوجبة" /> : <><ImagePlus /><strong>اختر صورة الوجبة</strong><span>JPG أو PNG</span></>}<input type="file" accept="image/*" onChange={(e) => choose(e.target.files[0])} /></label>{file && <button className="button wide" onClick={detect} disabled={detecting}>{detecting ? <><LoaderCircle className="spin" /> جارٍ اكتشاف المكونات...</> : <><Sparkles /> اكتشاف المكونات</>}</button>}</section>
      <section className="card ingredients-card"><div className="section-title"><ClipboardCheck /><div><h2>المكونات والكميات</h2><p>عدّل الاسم وحدد الوزن بالجرام قبل التحليل</p></div></div>{notice && <div className="demo-notice"><BrainCircuit />{notice}</div>}<div className="ingredient-list">{ingredients.map((ingredient, index) => <div key={`${ingredient.name}-${index}`}><Utensils /><input value={ingredient.name} aria-label={`اسم المكون ${index + 1}`} onChange={(e) => setIngredients(ingredients.map((value, i) => i === index ? { ...value, name: e.target.value } : value))} /><label className="ingredient-amount"><input type="number" min="1" max="5000" step="1" value={ingredient.amount_g} aria-label={`كمية ${ingredient.name} بالجرام`} onChange={(e) => setIngredients(ingredients.map((value, i) => i === index ? { ...value, amount_g: Number(e.target.value) } : value))} /><span>جم</span></label><button onClick={() => setIngredients(ingredients.filter((_, i) => i !== index))} aria-label="حذف المكون"><X /></button></div>)}</div><div className="add-ingredient"><input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="أضف مكوناً" onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addIngredient(); } }} /><button onClick={addIngredient}><Plus /></button></div><button className="button wide" disabled={!ingredients.length || ingredients.some((item) => !item.name.trim() || item.amount_g < 1 || item.amount_g > 5000) || loading} onClick={analyze}><Check /> تأكيد الكميات وتحليلها</button></section></div>
    {loading && <StagedLoader stage={stage} />}{error && <div className="inline-error">{error}</div>}<AnswerView answer={answer} onTechnical={(traceId) => { sessionStorage.setItem("afiyati_trace_id", traceId); navigate("/technical-demo"); }} />
    <div className="safety-notice"><ShieldCheck /><div><strong>مرحلتان منفصلتان</strong><p>اكتشاف الطعام لا يقدم توصية طبية. التحليل يبدأ فقط بعد تأكيدك للمكونات ثم يسترجع الدليل.</p></div></div>
  </AppShell>;
}

const habits = [
  ["القهوة والكافيين", Coffee, "أسأل عن تأثير القهوة والكافيين على حالاتي المسجلة."],
  ["النوم", BedDouble, "كيف يؤثر نمط نومي على حالاتي الصحية؟"],
  ["المشي", Footprints, "ما الإرشادات المتاحة للمشي مع حالاتي الصحية؟"],
  ["التمارين", Dumbbell, "ما الإرشادات المتاحة للتمارين مع حالاتي الصحية؟"],
  ["التدخين", CigaretteOff, "ما أثر التدخين وما إرشادات الإقلاع لحالاتي؟"],
];

export function HabitsPage() {
  const [selected, setSelected] = useState(habits[0]); const [context, setContext] = useState(""); const navigate = useNavigate(); const { answer, loading, stage, error, ask } = useGroundedQuestion();
  const submit = async (event) => { event.preventDefault(); const result = await ask({ question: `${selected[2]} السياق: ${context || "غير محدد"}`, mode: "habit" }); if (result?.emergency) navigate("/emergency", { state: { triggered: true } }); };
  return <AppShell title="تحليل العادات" eyebrow="سياقك اليومي مع الدليل"><div className="habit-layout"><section className="habit-picker">{habits.map((habit) => { const Icon = habit[1]; return <button key={habit[0]} onClick={() => setSelected(habit)} className={selected[0] === habit[0] ? "active" : ""}><Icon /><span>{habit[0]}</span><ChevronLeft /></button>; })}</section><form className="card habit-form" onSubmit={submit}><span className="large-icon">{(() => { const Icon = selected[1]; return <Icon />; })()}</span><h2>{selected[0]}</h2><p>أضف الكمية أو التكرار أو المدة لتحسين استرجاع الأدلة، دون اعتبارها تشخيصاً.</p><label>تفاصيل العادة<textarea rows="5" value={context} onChange={(e) => setContext(e.target.value)} placeholder="مثال: أشرب كوبين قهوة يومياً، واحد صباحاً والآخر بعد الظهر" /></label><button className="button wide" disabled={loading}><Search /> ابحث في الإرشادات</button></form></div>{loading && <StagedLoader stage={stage} />}{error && <div className="inline-error">{error}</div>}<AnswerView answer={answer} onTechnical={(traceId) => { sessionStorage.setItem("afiyati_trace_id", traceId); navigate("/technical-demo"); }} /></AppShell>;
}

export function SymptomsPage() {
  const [form, setForm] = useState({ symptoms: "", started_at: "", severity: 4, context: "" }); const [result, setResult] = useState(null); const [error, setError] = useState(""); const [loading, setLoading] = useState(false); const navigate = useNavigate();
  const submit = async (event) => { event.preventDefault(); setLoading(true); setError(""); try { const data = await api("/symptoms", { method: "POST", body: JSON.stringify({ ...form, severity: Number(form.severity) }) }); if (data.emergency) navigate("/emergency", { state: { triggered: true } }); else setResult(data); } catch (err) { setError(err.message); } finally { setLoading(false); } };
  return <AppShell title="تسجيل الأعراض" eyebrow="فرز آمن دون تشخيص"><div className="symptom-layout"><form className="card symptom-form" onSubmit={submit}><div className="section-title"><Activity /><div><h2>صف ما تشعر به</h2><p>اكتب الأعراض ووقت بدايتها وشدتها.</p></div></div><label>الأعراض<textarea required rows="4" value={form.symptoms} onChange={(e) => setForm({ ...form, symptoms: e.target.value })} placeholder="مثال: صداع ودوخة منذ الصباح" /></label><div className="form-grid"><label>وقت البداية<input type="datetime-local" value={form.started_at} onChange={(e) => setForm({ ...form, started_at: e.target.value })} /></label><label>الشدة: <strong>{form.severity}/10</strong><input type="range" min="1" max="10" value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })} /></label></div><label>سياق إضافي<textarea rows="3" value={form.context} onChange={(e) => setForm({ ...form, context: e.target.value })} placeholder="ما الذي كنت تفعله؟ هل تتفاقم الأعراض؟" /></label>{error && <p className="form-error">{error}</p>}<button className="button wide" disabled={loading}>{loading ? "جارٍ فرز الأعراض..." : "متابعة آمنة"}</button></form><aside className="triage-guide"><div><span className="monitoring"><CircleGauge /></span><h3>مراقبة</h3><p>أعراض خفيفة ومستقرة.</p></div><div><span className="professional"><Clock3 /></span><h3>تقييم مهني</h3><p>أعراض مستمرة أو متوسطة.</p></div><div><span className="emergency"><Siren /></span><h3>طوارئ محتملة</h3><p>يوقف المحادثة ويعرض الإجراء فوراً.</p></div></aside></div>{result && <div className="card triage-result"><CheckCircle2 /><div><h2>{result.classification === "monitoring" ? "المراقبة والتسجيل" : "ينصح بتقييم مهني"}</h2><p>{result.message}</p></div></div>}<div className="emergency-inline"><AlertOctagon /><div><strong>ألم صدر شديد، صعوبة تنفس، فقدان وعي، نزيف شديد؟</strong><p>لا تنتظر نموذج الفرز.</p></div><Link to="/emergency">طوارئ الآن</Link></div></AppShell>;
}

export function EmergencyPage() {
  const location = useLocation();
  return <main className="emergency-page" dir="rtl"><div className="emergency-content"><span className="emergency-symbol"><AlertOctagon /></span><p className="emergency-kicker">{location.state?.triggered ? "تم رصد مؤشرات طارئة" : "وضع الطوارئ"}</p><h1>قد تحتاج إلى مساعدة طبية عاجلة</h1><p className="emergency-lead">اتصل بخدمات الطوارئ المحلية الآن. لا تنتظر رد الذكاء الاصطناعي ولا تقد السيارة بنفسك.</p><a className="call-button" href="tel:123"><PhoneCall /> اتصل بالإسعاف 123 <span>مصر</span></a><div className="critical-grid"><span><Activity /> ألم شديد في الصدر</span><span><Activity /> صعوبة في التنفس</span><span><Activity /> فقدان الوعي</span><span><Activity /> نزيف شديد</span></div><p className="emergency-support">إن أمكن، اطلب من شخص قريب البقاء معك وفتح الباب للمسعفين.</p><Link className="safe-back" to="/">أنا بخير، العودة <ArrowLeft /></Link></div></main>;
}

function TraceChunk({ item, rank }) {
  return <article className="trace-chunk"><span className="trace-rank">#{rank}</span><div><strong>{item.metadata?.guideline_title || item.metadata?.source_filename}</strong><p>{item.text?.slice(0, 260)}</p><code>{item.metadata?.chunk_id}</code></div><span className="score">{item.rerank_score?.toFixed?.(4) || item.score?.toFixed?.(4)}</span></article>;
}

export function TechnicalDemoPage() {
  const [status, setStatus] = useState(null); const [benchmark, setBenchmark] = useState(null); const [trace, setTrace] = useState(null); const [error, setError] = useState(""); const traceId = sessionStorage.getItem("afiyati_trace_id");
  useEffect(() => { const calls = [api("/rag/status"), api("/rag/benchmark")]; if (traceId) calls.push(api(`/rag/traces/${traceId}`)); Promise.all(calls).then(([statusData, benchmarkData, traceData]) => { setStatus(statusData); setBenchmark(benchmarkData); setTrace(traceData || null); }).catch((err) => setError(err.message)); }, [traceId]);
  const primaryStrategy = benchmark?.retrieval?.primary_strategy; const benchmarkMetrics = primaryStrategy ? benchmark?.retrieval?.strategies?.[primaryStrategy] : null; const metric = (name) => { const value = benchmarkMetrics?.[name]?.value; return typeof value === "number" ? value.toFixed(3) : "—"; }; const groundingMetric = (name) => { const value = benchmark?.grounding?.[name]?.value; return typeof value === "number" ? value.toFixed(3) : "—"; };
  return <AppShell title="Technical RAG Demo" eyebrow="Judge-facing evidence trace"><div className="technical-header"><div><span className="tech-badge"><FlaskConical /> Retrieval-Augmented Generation</span><p>يعرض هذا القسم مصادر ومقاييس آمنة فقط — لا يعرض سلسلة التفكير الخاصة بالنموذج.</p></div><Link className="button" to="/ask">تشغيل سؤال جديد</Link></div>{error && <div className="inline-error">{error}</div>}
    <div className="status-grid technical-status"><div className="metric-card"><Database /><span>Indexed chunks</span><strong>{status?.indexed_chunks ?? "—"}</strong></div><div className="metric-card"><Search /><span>Retrieval</span><strong className="small-value">Hybrid RRF</strong></div><div className="metric-card"><BrainCircuit /><span>Embedding</span><strong className="small-value">{status?.embedding_model || "—"}</strong></div><div className="metric-card"><CircleGauge /><span>Top-K</span><strong>{status?.top_k ?? "—"}</strong></div></div>
    {!trace ? <div className="card source-empty"><FlaskConical /><div><h2>لا يوجد مسار سؤال بعد</h2><p>شغّل سؤالاً من شاشة «اسأل عافيتي». إذا كانت قاعدة المعرفة فارغة فسترى مسار رفض آمن بدون نتائج مختلقة.</p></div></div> : <div className="trace-stack">
      <section className="card trace-query"><span className="trace-step">01</span><div><small>Original query</small><h2>{trace.original_query}</h2><div className="query-chips">{trace.rewritten_queries?.map((query) => <span key={query}>{query}</span>)}</div></div></section>
      <section className="trace-columns"><div className="card"><div className="section-title"><Search /><div><h2>Query analysis</h2><p>Structured classification</p></div></div><dl className="tech-dl"><div><dt>Intent</dt><dd>{trace.analysis?.intent || "—"}</dd></div><div><dt>Topic</dt><dd>{trace.analysis?.topic || "—"}</dd></div><div><dt>Conditions</dt><dd>{trace.analysis?.conditions?.join(", ") || "—"}</dd></div><div><dt>Safety</dt><dd>{trace.safety?.classification || "—"}</dd></div></dl></div><div className="card"><div className="section-title"><CircleGauge /><div><h2>Measured latency</h2><p>Current request only</p></div></div><dl className="tech-dl">{Object.entries(trace.latency || {}).filter(([,value]) => typeof value === "number").map(([key,value]) => <div key={key}><dt>{key}</dt><dd>{value} ms</dd></div>)}</dl></div></section>
      <section className="card"><div className="section-title"><Database /><div><h2>Retrieved chunks</h2><p>Before reranking · {trace.retrieved_chunks?.length || 0} candidates</p></div></div><div className="trace-chunks">{trace.retrieved_chunks?.length ? trace.retrieved_chunks.map((item,index) => <TraceChunk item={item} rank={index + 1} key={item.metadata.chunk_id} />) : <p className="muted">No evidence retrieved.</p>}</div></section>
      <section className="card"><div className="section-title"><BrainCircuit /><div><h2>Reranked evidence</h2><p>Lexical fallback reranker · {trace.reranked_chunks?.length || 0} selected</p></div></div><div className="trace-chunks">{trace.reranked_chunks?.map((item,index) => <TraceChunk item={item} rank={index + 1} key={item.metadata.chunk_id} />)}</div></section>
      <section className="trace-columns"><div className="card"><div className="section-title"><FileCheck2 /><div><h2>Claims</h2><p>Automated grounding screen</p></div></div><div className="claim-list">{trace.claims?.length ? trace.claims.map((claim,index) => <div key={index} className={claim.status.toLowerCase()}><span>{claim.status === "SUPPORTED" ? <CheckCircle2 /> : claim.status === "NOT_EVALUATED_CROSS_LANGUAGE" ? <CircleGauge /> : <AlertTriangle />}</span><p>{claim.claim}</p><strong>{claim.status === "NOT_EVALUATED_CROSS_LANGUAGE" ? "CROSS-LANGUAGE REVIEW" : claim.status}</strong></div>) : <p className="muted">No generated claims to evaluate.</p>}</div></div><div className="card"><div className="section-title"><ClipboardCheck /><div><h2>Citation validation</h2><p>Metadata and retrieval membership</p></div></div><div className="coverage-number"><strong>{trace.citation_validation?.valid || 0} / {trace.citation_validation?.total || 0}</strong><span>metadata-valid citations</span></div><p className="metric-caveat">هذا فحص بنيوي للطلب الحالي، وليس «دقة استشهاد» سريرية مقاسة على مجموعة تقييم.</p></div></section>
    </div>}
    <section className={`card benchmark-panel ${benchmark?.dataset?.clinical_adjudication ? "official" : "provisional"}`}><div className="benchmark-heading">{benchmark?.dataset?.clinical_adjudication ? <CheckCircle2 /> : <AlertTriangle />}<div><h2>Benchmark metrics</h2><p>{benchmark?.evaluation_status || "Loading benchmark report..."}</p></div><span>{primaryStrategy || "pending"}</span></div>{benchmark?.retrieval?.status === "evaluated" ? <><div className="benchmark-metrics"><div><span>Precision@3</span><strong>{metric("precision_at_3")}</strong></div><div><span>Precision@5</span><strong>{metric("precision_at_5")}</strong></div><div><span>Recall@5</span><strong>{metric("recall_at_5")}</strong></div><div><span>MRR</span><strong>{metric("mrr")}</strong></div><div><span>Citation accuracy</span><strong>{groundingMetric("citation_accuracy")}</strong></div><div><span>Unsupported claims</span><strong>{groundingMetric("unsupported_claim_rate")}</strong></div></div><p className="metric-caveat">{benchmark.dataset?.judged_questions || 0} page-level judged questions · 95% bootstrap confidence intervals are stored in the machine-readable report. Official clinical claims remain blocked until independent clinician adjudication.</p></> : <p className="benchmark-empty">{benchmark?.retrieval?.reason || benchmark?.retrieval?.status || "Run the benchmark after indexing the guideline corpus."}</p>}</section>
  </AppShell>;
}
