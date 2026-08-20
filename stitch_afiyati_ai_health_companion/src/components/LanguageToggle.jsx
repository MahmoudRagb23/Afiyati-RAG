import { Languages } from "lucide-react";
import { useLanguage } from "../state/LanguageContext";

export default function LanguageToggle({ className = "" }) {
  const { isEnglish, toggleLocale, t } = useLanguage();
  return <button className={`language-toggle ${className}`.trim()} onClick={toggleLocale} type="button" aria-label={isEnglish ? "Switch to Arabic" : "Switch to English"}>
    <Languages size={17} />
    <span>{isEnglish ? t("language.switch") : "EN"}</span>
  </button>;
}
