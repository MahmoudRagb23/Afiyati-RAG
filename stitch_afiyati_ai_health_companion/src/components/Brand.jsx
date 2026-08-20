import { useLanguage } from "../state/LanguageContext";

export default function Brand({ compact = false, className = "" }) {
  const { isEnglish, t } = useLanguage();
  return <span className={`afiyati-brand ${compact ? "is-compact" : ""} ${className}`.trim()}>
    <span className="brand-symbol" aria-hidden="true">
      <svg viewBox="0 0 48 48" fill="none">
        <path d="M24 39.5c-8.8-5.5-14-11.4-14-18.5 0-4.7 3.3-8 7.5-8 2.9 0 5.3 1.5 6.5 3.8 1.2-2.3 3.6-3.8 6.5-3.8 4.2 0 7.5 3.3 7.5 8 0 7.1-5.2 13-14 18.5Z" fill="currentColor" opacity=".96" />
        <path d="M24 13.8v19.5M17.8 21.2h12.4" stroke="white" strokeWidth="2.6" strokeLinecap="round" />
      </svg>
    </span>
    <span className="brand-copy">
      <strong>{isEnglish ? t("brand.name") : "عافيتي"}</strong>
      {!compact && <small>{t("brand.tagline", "رفيقة صحتك اليومية")}</small>}
    </span>
  </span>;
}
