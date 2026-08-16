import {
  AlertTriangle,
  CalendarDays,
  Check,
  Clock3,
  Edit3,
  Plus,
  Pill,
  ShieldAlert,
  SkipForward,
  Trash2,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import AppShell from "../components/AppShell";

const foodLabels = { before_food: "قبل الطعام", after_food: "بعد الطعام", with_food: "مع الطعام", any: "مع أو بدون طعام" };
const statusLabels = { upcoming: "قادمة", taken: "تم أخذها", missed: "فائتة", skipped: "تم تخطيها" };

export function MedicationsPage() {
  const [medications, setMedications] = useState([]); const [schedule, setSchedule] = useState([]); const [error, setError] = useState(""); const [loading, setLoading] = useState(true);
  const load = () => Promise.all([api("/medications"), api("/medications/schedule/today")]).then(([meds, doses]) => { setMedications(meds); setSchedule(doses); }).catch((err) => setError(err.message)).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);
  const record = async (dose, status) => { try { await api(`/medications/${dose.medication_id}/dose`, { method: "POST", body: JSON.stringify({ scheduled_at: dose.scheduled_at, status }) }); await load(); } catch (err) { setError(err.message); } };
  const stop = async (id) => { if (!window.confirm("هل تريد إيقاف التذكيرات لهذا الدواء؟ لن يتم حذف سجل الجرعات.")) return; try { await api(`/medications/${id}`, { method: "DELETE" }); await load(); } catch (err) { setError(err.message); } };
  const adherence = useMemo(() => { const done = schedule.filter((item) => item.status === "taken").length; const completed = schedule.filter((item) => ["taken", "missed", "skipped"].includes(item.status)).length; return completed ? Math.round((done / completed) * 100) : null; }, [schedule]);
  return <AppShell title="أدويتي وجدولي العلاجي" eyebrow="تتبع فقط — لا تعديل ذاتي للجرعات">
    <div className="page-toolbar"><p>تابع الأدوية التي وصفها طبيبك ومواعيد الجرعات اليومية.</p><Link className="button" to="/medications/new"><Plus /> إضافة دواء</Link></div>
    {error && <div className="inline-error">{error}</div>}
    {loading ? <div className="card loading-card">جارٍ تحميل جدولك...</div> : <div className="medication-layout">
      <section className="card schedule-card"><div className="section-title"><CalendarDays /><div><h2>جدول اليوم</h2><p>{new Date().toLocaleDateString("ar-EG", { weekday: "long", day: "numeric", month: "long" })}</p></div>{adherence !== null && <span className="adherence">التزام {adherence}%</span>}</div>
        {schedule.length ? <div className="dose-timeline">{schedule.map((dose) => <article key={`${dose.medication_id}-${dose.scheduled_at}`} className={`dose-row ${dose.status}`}><time>{new Date(dose.scheduled_at).toLocaleTimeString("ar-EG", { hour: "2-digit", minute: "2-digit" })}</time><span className="timeline-dot" /><div className="dose-info"><span className={`status-chip ${dose.status}`}>{statusLabels[dose.status]}</span><h3>{dose.name} — {dose.dose}</h3><p>{foodLabels[dose.food_relation]}</p></div>{dose.status === "upcoming" && <div className="dose-buttons"><button className="button small" onClick={() => record(dose, "taken")}><Check /> تم أخذ الجرعة</button><button className="button secondary small" onClick={() => record(dose, "skipped")}><SkipForward /> تخطي</button><button className="text-button" onClick={() => record(dose, "missed")}>تسجيل كفائتة</button></div>}</article>)}</div> : <div className="empty-state"><Pill /><h3>لا توجد جرعات اليوم</h3><p>أضف دواءً موصوفاً لإنشاء المواعيد.</p></div>}
      </section>
      <section className="card active-medications"><div className="section-title"><Pill /><div><h2>الأدوية المسجلة</h2><p>{medications.filter((item) => item.active).length} نشطة</p></div></div>
        <div className="medication-list">{medications.length ? medications.map((med) => <article key={med.id} className={!med.active ? "inactive" : ""}><span className="pill-icon"><Pill /></span><div><h3>{med.name}</h3><p>{med.dose} · {med.frequency} مرة يومياً</p><small>{med.is_permanent ? "دائم" : `حتى ${med.end_date}`} · {foodLabels[med.food_relation]}</small></div><span className={`status-chip ${med.active ? "taken" : "skipped"}`}>{med.active ? "نشط" : "متوقف"}</span>{med.active && <div className="row-actions"><Link to={`/medications/${med.id}/edit`} aria-label="تعديل"><Edit3 /></Link><button onClick={() => stop(med.id)} aria-label="إيقاف"><Trash2 /></button></div>}</article>) : <p className="muted">لم تضف أدوية بعد.</p>}</div>
      </section>
    </div>}
    <div className="safety-notice"><ShieldAlert /><div><strong>تنبيه دوائي</strong><p>عافيتي أداة للتتبع والتذكير فقط. أي تغيير في الدواء أو الجرعة يحتاج مراجعة الطبيب أو الصيدلي.</p></div></div>
  </AppShell>;
}

const today = new Date().toISOString().slice(0, 10);
const emptyForm = { name: "", dose: "", frequency: 1, dose_times: ["08:00"], start_date: today, end_date: "", is_permanent: true, food_relation: "any", notes: "" };

export function MedicationFormPage() {
  const { id } = useParams(); const navigate = useNavigate(); const [form, setForm] = useState(emptyForm); const [error, setError] = useState(""); const [loading, setLoading] = useState(Boolean(id)); const [saving, setSaving] = useState(false);
  useEffect(() => { if (!id) return; api("/medications").then((items) => { const med = items.find((item) => item.id === Number(id)); if (!med) throw new Error("لم يتم العثور على الدواء"); setForm({ ...med, end_date: med.end_date || "" }); }).catch((err) => setError(err.message)).finally(() => setLoading(false)); }, [id]);
  const changeFrequency = (value) => { const count = Number(value); setForm((current) => ({ ...current, frequency: count, dose_times: Array.from({ length: count }, (_, index) => current.dose_times[index] || `${String(8 + index * Math.floor(12 / count)).padStart(2, "0")}:00`) })); };
  const submit = async (event) => { event.preventDefault(); setSaving(true); setError(""); try { await api(id ? `/medications/${id}` : "/medications", { method: id ? "PUT" : "POST", body: JSON.stringify({ ...form, frequency: Number(form.frequency), end_date: form.is_permanent ? null : form.end_date || null }) }); navigate("/medications"); } catch (err) { setError(err.message); } finally { setSaving(false); } };
  return <AppShell title={id ? "تعديل موعد الدواء" : "إضافة دواء جديد"} eyebrow="الدواء الموصوف من طبيبك فقط">
    {loading ? <div className="card loading-card">جارٍ تحميل الدواء...</div> : <form className="card medication-form" onSubmit={submit}>
      <div className="form-section"><div className="step-title"><span><Pill /></span><div><h2>معلومات الدواء</h2><p>انسخ الاسم والجرعة من الوصفة أو العبوة.</p></div></div><div className="form-grid"><label>اسم الدواء<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="مثال: Metformin" /></label><label>الجرعة<input required value={form.dose} onChange={(e) => setForm({ ...form, dose: e.target.value })} placeholder="مثال: 500mg" dir="ltr" /></label></div></div>
      <div className="form-section"><div className="step-title"><span><Clock3 /></span><div><h2>الجدول الزمني</h2><p>حدد عدد الجرعات والمواعيد كما وصفها الطبيب.</p></div></div><label>عدد المرات يومياً<select value={form.frequency} onChange={(e) => changeFrequency(e.target.value)}>{[1,2,3,4].map((n) => <option key={n} value={n}>{n}</option>)}</select></label><div className="time-grid">{form.dose_times.map((time, index) => <label key={index}>موعد {index + 1}<input type="time" required value={time} onChange={(e) => setForm((current) => ({ ...current, dose_times: current.dose_times.map((value, i) => i === index ? e.target.value : value) }))} /></label>)}</div><label>علاقة الجرعة بالطعام<select value={form.food_relation} onChange={(e) => setForm({ ...form, food_relation: e.target.value })}>{Object.entries(foodLabels).map(([value,label]) => <option value={value} key={value}>{label}</option>)}</select></label></div>
      <div className="form-section"><div className="step-title"><span><CalendarDays /></span><div><h2>فترة العلاج</h2><p>تنتهي تذكيرات الدواء المؤقت بعد تاريخ النهاية.</p></div></div><div className="segmented"><button type="button" className={form.is_permanent ? "active" : ""} onClick={() => setForm({ ...form, is_permanent: true, end_date: "" })}>دائم</button><button type="button" className={!form.is_permanent ? "active" : ""} onClick={() => setForm({ ...form, is_permanent: false })}>فترة محددة</button></div><div className="form-grid"><label>تاريخ البدء<input type="date" required value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} /></label>{!form.is_permanent && <label>تاريخ الانتهاء<input type="date" required min={form.start_date} value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} /></label>}</div><label>ملاحظات<textarea rows="3" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} placeholder="مثال: بعد الإفطار" /></label></div>
      <div className="medication-warning"><AlertTriangle /><p><strong>لا تضف دواءً أو تعدل جرعة بناءً على اقتراح الذكاء الاصطناعي.</strong> استخدم تعليمات مقدم الرعاية فقط.</p></div>{error && <p className="form-error">{error}</p>}<div className="form-actions"><button className="button" disabled={saving}>{saving ? "جارٍ الحفظ..." : "حفظ الدواء"}</button><Link className="button secondary" to="/medications">إلغاء</Link></div>
    </form>}
  </AppShell>;
}

