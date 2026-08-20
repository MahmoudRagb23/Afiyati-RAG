import { AlertTriangle, BookOpen, CheckCircle2, Coffee, Database, ExternalLink, ShieldCheck } from "lucide-react";
import { useState } from "react";

const conditionLabels = {
  hypertension: "ارتفاع ضغط الدم",
  type_2_diabetes: "السكري من النوع الثاني",
};

const statusLabels = {
  suitable: "مناسب وفق الدليل المتاح",
  caution: "ينصح بالحذر",
  not_recommended: "غير موصى به",
  insufficient_evidence: "أدلة غير كافية",
};

const nutrientLabels = {
  calories_kcal: "السعرات",
  carbohydrates_g: "الكربوهيدرات",
  sugars_g: "السكريات",
  fiber_g: "الألياف",
  protein_g: "البروتين",
  fat_g: "الدهون",
  saturated_fat_g: "الدهون المشبعة",
  sodium_mg: "الصوديوم",
  potassium_mg: "البوتاسيوم",
  caffeine_mg: "الكافيين",
};

const unitLabels = { KCAL: "سعر حراري", kcal: "سعر حراري", G: "جم", g: "جم", MG: "مجم", mg: "مجم" };

const healthActionLabels = {
  no_documented_harm: "لا ضرر خاص موثق",
  ask_quantity: "نحتاج الكمية أولاً",
  review_portion: "راجع الكمية",
  reduce: "قلّل",
  avoid: "تجنّب",
  needs_ingredients: "ثبّت المكونات",
  insufficient_evidence: "لا يوجد حكم خاص موثق",
};

function FoodSourceCard({ source, label }) {
  if (!source) return null;
  const content = <><Database /><div><span>{label}</span><strong>{source.title}</strong><small>{source.organization}</small><small>رقم السجل: {source.record_id} · {source.data_type} · {source.license}</small></div>{source.url && <ExternalLink />}</>;
  return source.url
    ? <a className="food-source" href={source.url} target="_blank" rel="noreferrer">{content}</a>
    : <div className="food-source">{content}</div>;
}

function SourceComparison({ comparison, primaryTitle, secondaryTitle }) {
  if (!comparison?.shared_nutrients?.length) return null;
  return <div className="source-comparison">
    <div><strong>مقارنة مستقلة بين المصدرين</strong><span>{comparison.note}</span></div>
    <div className="comparison-table">
      <div className="comparison-head"><span>العنصر</span><span>{primaryTitle}</span><span>{secondaryTitle}</span></div>
      {comparison.shared_nutrients.slice(0, 8).map((nutrient) => <div key={nutrient.key}><span>{nutrientLabels[nutrient.key] || nutrient.key}</span><strong>{nutrient.primary_value} {unitLabels[nutrient.primary_unit] || nutrient.primary_unit}</strong><strong>{nutrient.secondary_value} {unitLabels[nutrient.secondary_unit] || nutrient.secondary_unit}</strong></div>)}
    </div>
  </div>;
}

function NutritionPanel({ items = [], notices = [] }) {
  if (!items.length && !notices.length) return null;
  return (
    <section className="nutrition-panel">
      <div className="section-title"><Coffee /><div><h2>بيانات الطعام والمشروبات</h2><p>قيم مباشرة من قواعد رسمية وليست تقديراً من النموذج</p></div></div>
      <div className="nutrition-list">
        {items.map((item) => (
          <article className="nutrition-item" key={`${item.source.record_id}-${item.requested_name}`}>
            <div className={`source-verification ${item.source_count > 1 ? "verified" : "single"}`}><ShieldCheck /><div><strong>{item.source_count > 1 ? "تم التحقق من مصدرين رسميين مستقلين" : "مصدر رسمي واحد متاح لهذا التطابق"}</strong><span>{item.source_count > 1 ? "نعرض كل قيمة كما وردت في مصدرها دون دمج أو أخذ متوسط." : "لم نجد تطابقاً مستقلاً كافياً في المصدر الثاني، لذلك لا ندّعي تحققاً مزدوجاً."}</span></div></div>
            <div className="nutrition-heading"><div><span>{item.category === "beverage" ? "مشروب" : "طعام"}</span><h3>{item.requested_name}</h3><p>السجل المطابق: {item.matched_name}</p></div><strong>{item.basis}</strong></div>
            <div className="nutrient-grid">
              {Object.entries(item.nutrients || {}).map(([key, nutrient]) => (
                <div key={key}><span>{nutrientLabels[key] || key}</span><strong>{nutrient.value} <small>{unitLabels[nutrient.unit] || nutrient.unit}</small></strong></div>
              ))}
            </div>
            <div className="food-source-list">
              <FoodSourceCard source={item.source} label="المصدر الأساسي للقيم المعروضة" />
              {(item.supporting_sources || []).map((supporting) => <FoodSourceCard key={`${supporting.source.record_id}-${supporting.source.title}`} source={supporting.source} label="مصدر التحقق المستقل" />)}
            </div>
            <SourceComparison comparison={item.source_comparison} primaryTitle={item.source.title} secondaryTitle={item.supporting_sources?.[0]?.source?.title} />
          </article>
        ))}
      </div>
      {!!notices.length && <div className="food-notices">{notices.map((notice) => <p key={notice}><AlertTriangle />{notice}</p>)}</div>}
    </section>
  );
}

function HealthImpactPanel({ impacts = [] }) {
  if (!impacts.length) return null;
  return (
    <section className="health-impact-panel">
      <div className="section-title"><ShieldCheck /><div><h2>تأثير الطعام على حالتك المسجلة</h2><p>قاعدة قرار منفصلة عن النموذج، ومربوطة بالمصادر الطبية الظاهرة.</p></div></div>
      <div className="health-impact-list">
        {impacts.map((impact) => (
          <article className="health-impact-item" key={`${impact.food_name}-${impact.amount_g || "unknown"}`}>
            <div className="health-impact-heading"><div><span>{impact.category === "beverage" ? "مشروب" : impact.category === "mixed_dish" ? "طبق مركب" : "طعام"}</span><h3>{impact.food_name}</h3><p>{impact.meal_groups?.length ? impact.meal_groups.map((group) => group.label).join(" · ") : "تصنيف قيد المراجعة"}</p></div>{impact.amount_provided && <strong>{impact.amount_g} جم</strong>}</div>
            <div className="impact-assessment-list">
              {(impact.assessments || []).map((assessment) => (
                <div className={`impact-assessment action-${assessment.action}`} key={assessment.condition}>
                  <div className="impact-assessment-top"><strong>{assessment.condition_label || conditionLabels[assessment.condition]}</strong><span>{assessment.action_label || healthActionLabels[assessment.action]}</span></div>
                  <p>{assessment.assessment}</p><p className="impact-advice">{assessment.advice}</p>
                  {assessment.question && <div className="impact-question">{assessment.question}</div>}
                  {!!assessment.sources?.length && <div className="health-source-links">{assessment.sources.map((source) => <a key={source.id} href={source.url} target="_blank" rel="noreferrer"><BookOpen /><span><strong>{source.organization}</strong><small>{source.title} · {source.section}</small></span><ExternalLink /></a>)}</div>}
                </div>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function CitationPanel({ citations = [] }) {
  if (!citations.length) return null;
  return (
    <section className="citation-panel" id="answer-sources">
      <div className="section-title"><BookOpen /><div><h2>مصادر التقييم الصحي</h2><p>المراجع التي استشهدت بها الإجابة فعلياً</p></div></div>
      <div className="citation-list">
        {citations.map((citation) => (
          <article key={citation.chunk_id}>
            <div><strong>{citation.document}</strong><span>{citation.organization}</span><small>{citation.section || "قسم غير محدد"} · ص. {citation.page || "—"}</small></div>
            {citation.source_url && <a href={citation.source_url} target="_blank" rel="noreferrer" aria-label="فتح المصدر"><ExternalLink /></a>}
          </article>
        ))}
      </div>
    </section>
  );
}

export function EvidencePanel({ evidence = [] }) {
  if (!evidence.length) return null;
  return (
    <section className="evidence-panel" id="answer-top-k">
      <div className="section-title"><BookOpen /><div><h2>المقاطع المسترجعة (Top-K)</h2><p>المقاطع التي استندت إليها الإجابة، مرتبة للاطلاع فقط.</p></div></div>
      <div className="evidence-list">
        {evidence.map((item) => (
          <article className="evidence-item" key={item.chunk_id}>
            <div className="evidence-rank">#{item.rank}</div>
            <div className="evidence-body">
              <div className="evidence-meta">
                <strong>{item.document}</strong>
                <span>{item.organization}</span>
                <span>{item.section || "قسم غير محدد"}</span>
                <span>ص. {item.page || "—"}</span>
              </div>
              <p>{item.excerpt}</p>
              <code>{item.chunk_id}</code>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function AnswerReferenceControls({ hasSources, hasEvidence, onShowSources, onShowEvidence }) {
  if (!hasSources && !hasEvidence) return null;
  return <nav className="answer-reference-controls" aria-label="مراجع الإجابة">
    <span>تفاصيل الإجابة</span>
    {hasSources && <button type="button" onClick={onShowSources}><BookOpen /> المصادر الطبية</button>}
    {hasEvidence && <button type="button" onClick={onShowEvidence}><Database /> مقاطع Top-K</button>}
  </nav>;
}

export default function AnswerView({ answer, onTechnical }) {
  const [showSources, setShowSources] = useState(false);
  const [showEvidence, setShowEvidence] = useState(false);
  const reveal = (sectionId, setter) => {
    setter(true);
    window.requestAnimationFrame(() => document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth", block: "start" }));
  };
  if (!answer) return null;
  return (
    <div className="answer-stack">
      <section className={`answer-hero status-${answer.recommendation_status}`}>
        <div className="answer-icon"><ShieldCheck /></div>
        <div>{answer.greeting && <p className="answer-greeting">{answer.greeting}</p>}<span className="status-label">{answer.source_follow_up ? "المصادر المستخدمة" : statusLabels[answer.recommendation_status]}</span><h2>{answer.summary}</h2></div>
      </section>
      <NutritionPanel items={answer.nutrition_items} notices={answer.food_lookup_notices} />
      <HealthImpactPanel impacts={answer.food_health_impacts} />
      {!answer.food_health_impacts?.length && !!answer.conditions_considered?.length && (
        <section className="card">
          <div className="section-title"><CheckCircle2 /><div><h2>التأثير حسب حالتك</h2><p>تمت مراعاة الحالات المسجلة</p></div></div>
          <div className="condition-results">
            {answer.conditions_considered.map((item) => (
              <article key={item.condition}><strong>{conditionLabels[item.condition] || item.condition}</strong><p>{item.assessment}</p></article>
            ))}
          </div>
        </section>
      )}
      {answer.suggested_quantity && (
        <section className="quantity-card"><strong>الكمية المدعومة بالدليل</strong><span>{answer.suggested_quantity.value}</span><p>{answer.suggested_quantity.basis}</p></section>
      )}
      {!!answer.warnings?.length && (
        <section className="warning-card"><AlertTriangle /><div><strong>تنبيهات مهمة</strong>{answer.warnings.map((warning) => <p key={warning}>{warning}</p>)}</div></section>
      )}
      <AnswerReferenceControls
        hasSources={!!answer.citations?.length}
        hasEvidence={!!answer.evidence?.length}
        onShowSources={() => reveal("answer-sources", setShowSources)}
        onShowEvidence={() => reveal("answer-top-k", setShowEvidence)}
      />
      {showSources && <CitationPanel citations={answer.citations} />}
      {showEvidence && <EvidencePanel evidence={answer.evidence} />}
      {onTechnical && answer.trace_id && (
        <button className="button secondary" onClick={() => onTechnical(answer.trace_id)}><ExternalLink size={18} /> فتح العرض التقني</button>
      )}
    </div>
  );
}
