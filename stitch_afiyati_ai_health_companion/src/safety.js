const emergencyPatterns = [
  /(?:ألم|وجع|ضغط).{0,18}(?:شديد )?(?:في|على).{0,10}(?:الصدر|قلبي)/i,
  /(?:مش قادر|مش عارف|لا أستطيع).{0,14}(?:أتنفس|اتنفس|آخذ نفس|اخد نفس)/i,
  /(?:ضيق نفس|صعوبة.{0,8}التنفس|اختناق|باختنق|بختنق|نفسي مخنوق|نفسي قاطع)/i,
  /(?:cannot|can not|can't).{0,15}breathe|difficulty breathing|shortness of breath|choking|gasping/i,
  /(?:فقد(?:ت|ان)? الوعي|مغمى عليه|أغمي علي|اغمى علي|unconscious|loss of consciousness|fainted?)/i,
  /(?:اعوجاج الوجه|ثقل الكلام|ضعف مفاجئ|تنميل مفاجئ|خدر مفاجئ|مش قادر.{0,8}اتكلم|cannot speak clearly|face droop|one.side weakness)/i,
  /(?:نزيف شديد|نزيف لا يتوقف|ترجيع دم|قيء دم|براز أسود|براز اسود|severe bleeding|vomiting blood|black stool)/i,
  /(?:تورم.{0,12}(?:اللسان|الشفايف|الشفتين|الحلق)|حساسية شديدة|anaphylaxis|swollen (?:tongue|lips|throat))/i,
];

export function isEmergencyMessage(value = "") {
  return emergencyPatterns.some((pattern) => pattern.test(value));
}

const symptomCheckInPattern = /(?:عندي|حاسس|حاسة|بحس|حسيت|أشعر|اشعر|عندي(?:ه)?|i have|i feel|i'm feeling|im feeling).{0,90}(?:صداع|دوخة|دوار|غثيان|خفقان|تعب|إرهاق|ارهاق|حرارة|زغللة|زغلله|ألم|وجع|تنميل|ضعف|headache|dizz(?:y|iness)|nausea|palpitation|fatigue|fever|blurred vision|pain|numbness|weakness)/i;

export function isSymptomCheckIn(value = "") {
  return symptomCheckInPattern.test(value);
}
