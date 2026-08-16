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

const loadingStages = ["أبحث في الإرشادات الطبية...", "أراجع المعلومات المتعلقة بحالتك...", "أتحقق من المصادر...", "أجهز الإجابة الآمنة..."];

function StagedLoader({ stage }) {
  return <div className="staged-loader"><div className="scan-orbit"><Search /><i /></div><div><strong>{loadingStages[stage]}</strong><span>{stage + 1} من {loadingStages.length}</span><div className="stage-progress"><i style={{ width: `${((stage + 1) / loadingStages.length) * 100}%` }} /></div></div></div>;
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

export function AskPage() {
  const [question, setQuestion] = useState(""); const navigate = useNavigate(); const inputRef = useRef(null); const { answer, loading, stage, error, ask } = useGroundedQuestion();
  const submit = async (event) => { event.preventDefault(); if (question.trim()) await ask({ question, mode: "chat" }); };
  const examples = ["هل أقدر أشرب قهوتين في اليوم؟", "هل الموز مناسب لحالتي؟", "كيف يؤثر المشي على حالاتي الصحية؟"];
  return <AppShell title="اسأل عافيتي" eyebrow="إجابة من الدليل، لا من الذاكرة">
    <div className="ask-layout">
      <section className="ask-main card"><div className="assistant-intro"><span><Bot /></span><div><h2>ما الذي تريد فهمه اليوم؟</h2><p>اسأل عن طعام أو عادة أو إرشاد عام. الأسئلة الدوائية لا تغير وصفتك.</p></div></div>
        {!answer && !loading && <div className="prompt-examples">{examples.map((example) => <button key={example} onClick={() => { setQuestion(example); inputRef.current?.focus(); }}><MessageCircleQuestion />{example}<ChevronLeft /></button>)}</div>}
        {loading && <StagedLoader stage={stage} />}{error && <div className="inline-error"><AlertTriangle />{error}</div>}
        <AnswerView answer={answer} onTechnical={(traceId) => { sessionStorage.setItem("afiyati_trace_id", traceId); navigate("/technical-demo"); }} />
        <form className="chat-composer" onSubmit={submit}><textarea ref={inputRef} rows="2" maxLength="2000" required value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="مثال: أنا عندي ضغط وسكري، هل القهوة مناسبة؟" /><button className="send-button" disabled={loading || !question.trim()} aria-label="إرسال السؤال">{loading ? <LoaderCircle className="spin" /> : <Send />}</button></form>
        <p className="composer-note"><ShieldCheck /> إذا لم توجد أدلة كافية في المصادر المفهرسة، سيرفض عافيتي إعطاء توصية.</p>
      </section>
      <aside className="ask-aside"><div className="card"><h3>ما الذي يُرسل للنموذج؟</h3><ol><li><span>1</span> سؤالك والحالات المسجلة</li><li><span>2</span> مقاطع الإرشادات المسترجعة</li><li><span>3</span> قواعد السلامة والرفض</li></ol></div><div className="safety-mini"><ShieldAlert /><p>لا تستخدم المحادثة في الطوارئ.</p><Link to="/emergency">افتح وضع الطوارئ</Link></div></aside>
    </div>
  </AppShell>;
}

export function MealPage() {
  const [file, setFile] = useState(null); const [preview, setPreview] = useState(""); const [ingredients, setIngredients] = useState([]); const [draft, setDraft] = useState(""); const [detecting, setDetecting] = useState(false); const [notice, setNotice] = useState(""); const navigate = useNavigate(); const { answer, loading, stage, error, ask } = useGroundedQuestion();
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);
  const choose = (selected) => { if (!selected) return; if (preview) URL.revokeObjectURL(preview); setFile(selected); setPreview(URL.createObjectURL(selected)); setIngredients([]); setNotice(""); };
  const detect = async () => { if (!file) return; setDetecting(true); const body = new FormData(); body.append("file", file); try { const result = await api("/meals/detect", { method: "POST", body }); setIngredients(result.ingredients); setNotice(result.notice); } catch (err) { setNotice(err.message); } finally { setDetecting(false); } };
  const addIngredient = () => { if (draft.trim()) { setIngredients([...ingredients, draft.trim()]); setDraft(""); } };
  const analyze = () => ask({ question: "حلل هذه الوجبة في ضوء حالاتي الصحية المسجلة.", confirmed_ingredients: ingredients, mode: "meal" });
  return <AppShell title="تحليل الوجبة" eyebrow="اكتشاف بصري ثم تأكيد بشري">
    <div className="meal-grid"><section className="card upload-card"><div className="section-title"><Camera /><div><h2>صورة الوجبة</h2><p>الصورة تستخدم لاكتشاف مكونات محتملة فقط</p></div></div><label className={`drop-zone ${preview ? "has-image" : ""}`}>{preview ? <img src={preview} alt="معاينة الوجبة" /> : <><ImagePlus /><strong>اختر صورة الوجبة</strong><span>JPG أو PNG</span></>}<input type="file" accept="image/*" onChange={(e) => choose(e.target.files[0])} /></label>{file && <button className="button wide" onClick={detect} disabled={detecting}>{detecting ? <><LoaderCircle className="spin" /> جارٍ اكتشاف المكونات...</> : <><Sparkles /> اكتشاف المكونات</>}</button>}</section>
      <section className="card ingredients-card"><div className="section-title"><ClipboardCheck /><div><h2>المكونات المكتشفة</h2><p>عدّل القائمة قبل أي تحليل صحي</p></div></div>{notice && <div className="demo-notice"><BrainCircuit />{notice}</div>}<div className="ingredient-list">{ingredients.map((ingredient, index) => <div key={`${ingredient}-${index}`}><Utensils /><input value={ingredient} onChange={(e) => setIngredients(ingredients.map((value, i) => i === index ? e.target.value : value))} /><button onClick={() => setIngredients(ingredients.filter((_, i) => i !== index))} aria-label="حذف المكون"><X /></button></div>)}</div><div className="add-ingredient"><input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="أضف مكوناً" onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addIngredient(); } }} /><button onClick={addIngredient}><Plus /></button></div><button className="button wide" disabled={!ingredients.length || loading} onClick={analyze}><Check /> تأكيد المكونات وتحليلها</button></section></div>
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
  const submit = (event) => { event.preventDefault(); ask({ question: `${selected[2]} السياق: ${context || "غير محدد"}`, mode: "habit" }); };
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
