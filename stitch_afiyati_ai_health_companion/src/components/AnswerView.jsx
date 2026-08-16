import { AlertTriangle, BookOpen, CheckCircle2, ExternalLink, ShieldCheck } from "lucide-react";

const conditionLabels = {
  hypertension: "ارتفاع ضغط الدم",
  type_2_diabetes: "السكري من النوع الثاني",
  chronic_kidney_disease: "مرض الكلى المزمن",
  asthma: "الربو",
};

const statusLabels = {
  suitable: "مناسب وفق الدليل المتاح",
  caution: "ينصح بالحذر",
  not_recommended: "غير موصى به",
  insufficient_evidence: "أدلة غير كافية",
};

export function EvidencePanel({ evidence = [] }) {
  if (!evidence.length) return null;
  return (
    <section className="evidence-panel">
      <div className="section-title"><BookOpen /><div><h2>الأدلة المسترجعة</h2><p>المقاطع التي استندت إليها الإجابة</p></div></div>
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
            <span className="score">{item.relevance?.toFixed?.(3) || item.relevance}</span>
          </article>
        ))}
      </div>
    </section>
  );
}

export default function AnswerView({ answer, onTechnical }) {
  if (!answer) return null;
  return (
    <div className="answer-stack">
      <section className={`answer-hero status-${answer.recommendation_status}`}>
        <div className="answer-icon"><ShieldCheck /></div>
        <div><span className="status-label">{statusLabels[answer.recommendation_status]}</span><h2>{answer.summary}</h2></div>
      </section>
      {!!answer.conditions_considered?.length && (
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
      <div className="evidence-strength">
        <span>قوة الدليل</span><strong>{answer.evidence_strength}</strong>
        <small>لا تمثل نسبة ثقة طبية</small>
      </div>
      <EvidencePanel evidence={answer.evidence} />
      {onTechnical && answer.trace_id && (
        <button className="button secondary" onClick={() => onTechnical(answer.trace_id)}><ExternalLink size={18} /> فتح العرض التقني</button>
      )}
    </div>
  );
}

