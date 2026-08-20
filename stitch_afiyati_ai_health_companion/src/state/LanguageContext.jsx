import { createContext, useContext, useEffect, useMemo, useState } from "react";

const LanguageContext = createContext(null);

const english = {
  "brand.name": "Afiyati",
  "brand.tagline": "YOUR WELLNESS COMPANION",
  "language.switch": "العربية",
  "nav.home": "Dashboard",
  "nav.ask": "Chat",
  "nav.foodChat": "Food chat",
  "nav.meal": "Food",
  "nav.meds": "Medications",
  "nav.symptoms": "Symptoms",
  "nav.foodHistory": "Food history",
  "nav.history": "History",
  "nav.profile": "Profile",
  "nav.sources": "Sources",
  "nav.demo": "Technical demo",
  "nav.settings": "Settings",
  "nav.help": "Help & safety",
  "nav.emergency": "Emergency",
  "nav.signOut": "Sign out",
  "nav.welcome": "Welcome back",
  "nav.summary": "Your health summary",
  "common.loading": "Preparing Afiyati...",
  "landing.why": "Why Afiyati?",
  "landing.sources": "Medical sources",
  "landing.login": "Log in",
  "landing.start": "Get started",
  "landing.dashboard": "My dashboard",
  "landing.eyebrow": "An evidence-led health companion",
  "landing.hero": "Healthier days,",
  "landing.heroAccent": "with clearer choices.",
  "landing.lead": "A private health companion that connects your everyday questions with trusted medical guidance and clear sources.",
  "landing.how": "How it works",
  "landing.emergency": "Emergency now",
  "landing.previewGreeting": "Good morning, Ahmed",
  "landing.previewSub": "Your health snapshot for today",
  "landing.previewAsk": "Ask Afiyati",
  "landing.previewImpact": "Explore how coffee fits your routine",
  "landing.previewEvidence": "Trusted guidance",
  "landing.previewEvidenceValue": "Ready when you need it",
  "landing.previewConditions": "Supported conditions",
  "landing.previewConditionValue": "Blood pressure · Diabetes",
  "landing.previewSource": "Source-aware answers",
  "landing.previewSourceSub": "Open every source in one tap",
  "landing.safety": "Safety comes first",
  "landing.safetySub": "Emergency triage is immediate",
  "landing.whyEyebrow": "Trust you can inspect",
  "landing.whyTitle": "Why choose Afiyati?",
  "landing.whyLead": "Designed to make guidance, sources, and safety boundaries visible — never to replace your clinician.",
  "landing.featureEvidence": "Evidence-led",
  "landing.featureEvidenceLead": "Answers are grounded in the official guidance in your knowledge base.",
  "landing.featurePersonal": "Made for your profile",
  "landing.featurePersonalLead": "Uses your registered health context to keep responses relevant.",
  "landing.featureTrace": "Clear sources",
  "landing.featureTraceLead": "See direct references and the retrieved evidence behind every answer.",
  "landing.private": "Private, local, and thoughtful",
  "landing.privateLead": "Your data stays on your device while Afiyati helps you understand everyday choices.",
  "landing.openDemo": "Explore the evidence flow",
  "landing.disclaimer": "For education and lifestyle support only — never diagnosis or a prescription.",
  "auth.welcome": "Welcome back",
  "auth.join": "Start your Afiyati journey",
  "auth.lead": "Your health details are stored locally on this device in this prototype.",
  "auth.login": "Log in",
  "auth.register": "Create account",
  "auth.name": "Full name",
  "auth.email": "Email address",
  "auth.password": "Password",
  "auth.checking": "Checking securely...",
  "auth.loginAction": "Secure sign in",
  "auth.registerAction": "Create my account",
  "auth.note": "Your data is never sent to paid AI services.",
  "page.dashboard": "Your dashboard",
  "page.ask": "Ask Afiyati",
  "page.meal": "Meal analysis",
  "page.habits": "Habit insights",
  "page.symptoms": "Log symptoms",
  "page.profile": "Health profile",
  "eyebrow.dashboard": "Today at a glance",
  "eyebrow.ask": "Evidence, not guesswork",
  "eyebrow.meal": "Visual detection, then your confirmation",
  "eyebrow.habits": "Your everyday context, with evidence",
  "eyebrow.symptoms": "Safe triage, not diagnosis",
  "eyebrow.profile": "Safe personalisation",
  "ask.greeting": "Hello",
  "ask.intro": "I use your saved health context and recent conversation only to personalise the answer. Every recommendation remains linked to a visible source.",
  "ask.context": "Context in use",
  "ask.contextLead": "Your reported details personalise responses; they are not medical evidence.",
  "ask.edit": "Edit profile",
  "ask.emptyContext": "No conditions or allergies recorded",
  "ask.placeholder": "For example: I have high blood pressure and diabetes — is coffee suitable?",
  "ask.note": "For a more useful food answer, add the amount in grams, for example: 200 g banana.",
  "ask.how": "How is an answer built?",
  "ask.step1": "Understand your question and saved context",
  "ask.step2": "Check official food data where available",
  "ask.step3": "Retrieve guidance for your condition",
  "ask.step4": "Show direct records and references",
  "ask.sources": "View data policy and sources",
  "ask.safety": "Do not use chat in an emergency.",
  "ask.emergency": "Open emergency mode",
};

export function LanguageProvider({ children }) {
  const [locale, setLocale] = useState(() => localStorage.getItem("afiyati_locale") || "ar");

  useEffect(() => {
    const isEnglish = locale === "en";
    document.documentElement.lang = isEnglish ? "en" : "ar";
    document.documentElement.dir = isEnglish ? "ltr" : "rtl";
    document.title = isEnglish ? "Afiyati — clearer health choices" : "عافيتي — قرارات صحية أوضح";
    localStorage.setItem("afiyati_locale", locale);
  }, [locale]);

  const value = useMemo(() => ({
    locale,
    isEnglish: locale === "en",
    setLocale,
    toggleLocale: () => setLocale((current) => current === "ar" ? "en" : "ar"),
    t: (key, fallback = key) => locale === "en" ? (english[key] || fallback) : fallback,
  }), [locale]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export const useLanguage = () => useContext(LanguageContext);
