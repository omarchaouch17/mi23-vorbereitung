"""translations.py - alle sichtbaren Texte von MediLink in DE / EN / FR / AR.

Neue Texte immer in ALLEN vier Sprachen ergaenzen (test_app.py prueft das).
Platzhalter wie {label}, {low}, {high}, {p} werden mit str.format() gefuellt.
"""

diagnose_uebersetzung = {
    "Herzinsuffizienz": {"en": "Heart failure", "fr": "Insuffisance cardiaque", "ar": "قصور القلب"},
    "Appendizitis": {"en": "Appendicitis", "fr": "Appendicite", "ar": "التهاب الزائدة الدودية"},
    "Kolonkarzinom": {"en": "Colon cancer", "fr": "Cancer du côlon", "ar": "سرطان القولون"},
    "Hypertonie": {"en": "Hypertension", "fr": "Hypertension artérielle", "ar": "ارتفاع ضغط الدم"},
    "Diabetes mellitus": {"en": "Diabetes mellitus", "fr": "Diabète sucré", "ar": "داء السكري"},
    "Asthma": {"en": "Asthma", "fr": "Asthme", "ar": "الربو"},
    "Herzinfarkt": {"en": "Myocardial infarction", "fr": "Infarctus du myocarde", "ar": "احتشاء عضلة القلب"},
    "Krank": {"en": "Ill", "fr": "Malade", "ar": "مريض"},
    "Schlaganfall": {"en": "Stroke", "fr": "Accident vasculaire cérébral (AVC)", "ar": "السكتة الدماغية"},
    "COPD": {"en": "COPD", "fr": "BPCO", "ar": "مرض الانسداد الرئوي المزمن"},
    "Pneumonie": {"en": "Pneumonia", "fr": "Pneumonie", "ar": "الالتهاب الرئوي"},
    "Niereninsuffizienz": {"en": "Kidney failure", "fr": "Insuffisance rénale", "ar": "الفشل الكلوي"},
    "Migräne": {"en": "Migraine", "fr": "Migraine", "ar": "الصداع النصفي"},
    "Depression": {"en": "Depression", "fr": "Dépression", "ar": "الاكتئاب"},
}

# Auswahl im Formular "Neuer Patient" (deutscher Name wird gespeichert; "Krank" ist zu unspezifisch).
# Alles andere ueber die Option "Andere" mit freiem Textfeld.
DIAGNOSEN = [
    "Hypertonie", "Herzinsuffizienz", "Herzinfarkt", "Schlaganfall", "Diabetes mellitus",
    "Asthma", "COPD", "Pneumonie", "Niereninsuffizienz", "Migräne", "Depression",
    "Appendizitis", "Kolonkarzinom",
]
ANDERE = "__andere__"   # Wert der Option "Andere (selbst eingeben)"

texte = {
    "de": {
        "titel": "MediLink", "patienten": "Patienten", "diagnose": "Diagnose",
        "keine_diagnose": "Keine Diagnose",
        "neuer_patient_link": "+ Neuen Patienten hinzufügen",
        "risiko_link": "❤ Herzrisiko berechnen",
        "verlauf_link": "[Verlauf]", "loeschen": "[löschen]",
        "loeschen_frage": "Patient wirklich löschen?",
        "risiko_label": "Risiko",
        "risiko_titel": "Framingham-Risikoscore berechnen",
        "risiko_hinweis": "Nur zur Veranschaulichung - kein Diagnoseinstrument.",
        "berechnen": "Berechnen",
        "geschlecht": "Geschlecht", "maennlich": "Männlich", "weiblich": "Weiblich",
        "name": "Name", "alter": "Alter", "cholesterin": "Gesamtcholesterin",
        "hdl": "HDL-Cholesterin", "blutdruck": "Systolischer Blutdruck",
        "raucher": "Raucher", "behandelt": "Blutdruckbehandlung",
        "bereich": "Bereich", "zurueck": "Zurück zur Übersicht",
        "neu_titel": "Neuer Patient", "neu_name": "Patientenname",
        "neu_diagnose": "Diagnose", "neu_kategorie": "Kategorie", "speichern": "Speichern",
        "gespeichert": "Patient erfolgreich gespeichert.",
        "verlauf_titel": "Risiko-Verlauf", "datum": "Datum", "risiko_spalte": "Risiko",
        "kein_verlauf": "Noch keine Risiko-Berechnung für diesen Patienten.",
        "ergebnis": "Risiko berechnet: {p}% (10-Jahres-Risiko). Dies ist eine Abschätzung, kein Diagnoseinstrument.",
        "fehler_titel": "Bitte die rot markierten Felder korrigieren.",
        "err_required": "{label}: Pflichtfeld.",
        "err_number": "{label}: Bitte eine gültige Zahl eingeben.",
        "err_range": "{label} muss zwischen {low} und {high} liegen.",
        "err_hdl": "HDL muss kleiner als das Gesamtcholesterin sein.",
        "err_sex": "Bitte ein Geschlecht auswählen.",
        "err_long": "{label}: Maximal {max} Zeichen.",
        "waehlen": "Bitte wählen …",
        "err_choose": "{label}: Bitte eine Auswahl treffen.",
        "andere": "Andere (selbst eingeben)",
        "frei_label": "Eigene Diagnose",
    },
    "en": {
        "titel": "MediConnect", "patienten": "Patients", "diagnose": "Diagnosis",
        "keine_diagnose": "No diagnosis",
        "neuer_patient_link": "+ Add new patient",
        "risiko_link": "❤ Calculate heart risk",
        "verlauf_link": "[History]", "loeschen": "[delete]",
        "loeschen_frage": "Really delete this patient?",
        "risiko_label": "Risk",
        "risiko_titel": "Calculate Framingham Risk Score",
        "risiko_hinweis": "For illustration only - not a diagnostic tool.",
        "berechnen": "Calculate",
        "geschlecht": "Sex", "maennlich": "Male", "weiblich": "Female",
        "name": "Name", "alter": "Age", "cholesterin": "Total cholesterol",
        "hdl": "HDL cholesterol", "blutdruck": "Systolic blood pressure",
        "raucher": "Smoker", "behandelt": "Treated for high blood pressure",
        "bereich": "Range", "zurueck": "Back to overview",
        "neu_titel": "New patient", "neu_name": "Patient name",
        "neu_diagnose": "Diagnosis", "neu_kategorie": "Category", "speichern": "Save",
        "gespeichert": "Patient saved successfully.",
        "verlauf_titel": "Risk history", "datum": "Date", "risiko_spalte": "Risk",
        "kein_verlauf": "No risk calculation for this patient yet.",
        "ergebnis": "Risk calculated: {p}% (10-year risk). This is an estimate, not a diagnostic tool.",
        "fehler_titel": "Please correct the fields marked in red.",
        "err_required": "{label}: required field.",
        "err_number": "{label}: please enter a valid number.",
        "err_range": "{label} must be between {low} and {high}.",
        "err_hdl": "HDL must be lower than total cholesterol.",
        "err_sex": "Please select a sex.",
        "err_long": "{label}: maximum {max} characters.",
        "waehlen": "Please select …",
        "err_choose": "{label}: please make a selection.",
        "andere": "Other (enter yourself)",
        "frei_label": "Own diagnosis",
    },
    "fr": {
        "titel": "MédiLien", "patienten": "Patients", "diagnose": "Diagnostic",
        "keine_diagnose": "Aucun diagnostic",
        "neuer_patient_link": "+ Ajouter un patient",
        "risiko_link": "❤ Calculer le risque cardiaque",
        "verlauf_link": "[Historique]", "loeschen": "[supprimer]",
        "loeschen_frage": "Supprimer vraiment ce patient ?",
        "risiko_label": "Risque",
        "risiko_titel": "Calculer le score de risque de Framingham",
        "risiko_hinweis": "À titre d'illustration uniquement - pas un outil de diagnostic.",
        "berechnen": "Calculer",
        "geschlecht": "Sexe", "maennlich": "Homme", "weiblich": "Femme",
        "name": "Nom", "alter": "Âge", "cholesterin": "Cholestérol total",
        "hdl": "Cholestérol HDL", "blutdruck": "Pression artérielle systolique",
        "raucher": "Fumeur", "behandelt": "Traitement de l'hypertension",
        "bereich": "Plage", "zurueck": "Retour à l'aperçu",
        "neu_titel": "Nouveau patient", "neu_name": "Nom du patient",
        "neu_diagnose": "Diagnostic", "neu_kategorie": "Catégorie", "speichern": "Enregistrer",
        "gespeichert": "Patient enregistré avec succès.",
        "verlauf_titel": "Historique du risque", "datum": "Date", "risiko_spalte": "Risque",
        "kein_verlauf": "Aucun calcul de risque pour ce patient.",
        "ergebnis": "Risque calculé : {p} % (risque à 10 ans). Il s'agit d'une estimation, pas d'un outil de diagnostic.",
        "fehler_titel": "Veuillez corriger les champs marqués en rouge.",
        "err_required": "{label} : champ obligatoire.",
        "err_number": "{label} : veuillez saisir un nombre valide.",
        "err_range": "{label} doit être compris entre {low} et {high}.",
        "err_hdl": "Le HDL doit être inférieur au cholestérol total.",
        "err_sex": "Veuillez sélectionner un sexe.",
        "err_long": "{label} : {max} caractères maximum.",
        "waehlen": "Veuillez choisir …",
        "err_choose": "{label} : veuillez faire un choix.",
        "andere": "Autre (saisir soi-même)",
        "frei_label": "Diagnostic personnalisé",
    },
    "ar": {
        "titel": "رابط طبي", "patienten": "المرضى", "diagnose": "التشخيص",
        "keine_diagnose": "لا يوجد تشخيص",
        "neuer_patient_link": "+ إضافة مريض جديد",
        "risiko_link": "❤ حساب خطر القلب",
        "verlauf_link": "[السجل]", "loeschen": "[حذف]",
        "loeschen_frage": "هل تريد حذف هذا المريض فعلاً؟",
        "risiko_label": "الخطر",
        "risiko_titel": "حساب درجة خطر فرامنغهام",
        "risiko_hinweis": "للتوضيح فقط - ليست أداة تشخيصية.",
        "berechnen": "احسب",
        "geschlecht": "الجنس", "maennlich": "ذكر", "weiblich": "أنثى",
        "name": "الاسم", "alter": "العمر", "cholesterin": "الكوليسترول الكلي",
        "hdl": "الكوليسترول HDL", "blutdruck": "ضغط الدم الانقباضي",
        "raucher": "مدخّن", "behandelt": "علاج ارتفاع ضغط الدم",
        "bereich": "المدى", "zurueck": "العودة إلى القائمة",
        "neu_titel": "مريض جديد", "neu_name": "اسم المريض",
        "neu_diagnose": "التشخيص", "neu_kategorie": "الفئة", "speichern": "حفظ",
        "gespeichert": "تم حفظ المريض بنجاح.",
        "verlauf_titel": "سجل الخطر", "datum": "التاريخ", "risiko_spalte": "الخطر",
        "kein_verlauf": "لا يوجد حساب للخطر لهذا المريض بعد.",
        "ergebnis": "تم حساب الخطر: {p}% (خطر 10 سنوات). هذا تقدير وليس أداة تشخيصية.",
        "fehler_titel": "يرجى تصحيح الحقول المعلَّمة بالأحمر.",
        "err_required": "{label}: حقل مطلوب.",
        "err_number": "{label}: يرجى إدخال رقم صحيح.",
        "err_range": "{label} يجب أن تكون القيمة بين {low} و{high}.",
        "err_hdl": "يجب أن يكون HDL أقل من الكوليسترول الكلي.",
        "err_sex": "يرجى اختيار الجنس.",
        "err_long": "{label}: الحد الأقصى {max} حرفًا.",
        "waehlen": "يرجى الاختيار …",
        "err_choose": "{label}: يرجى الاختيار من القائمة.",
        "andere": "أخرى (أدخلها بنفسك)",
        "frei_label": "تشخيص آخر",
    },
}

# Auswahl fuer das Feld "Kategorie" (Fachgebiet). Gespeichert wird der deutsche Name
# (wie bei den bisherigen Eintraegen), angezeigt wird er in der gewaehlten Sprache.
kategorie_uebersetzung = {
    "Kardiologie": {"de": "Kardiologie", "en": "Cardiology", "fr": "Cardiologie", "ar": "أمراض القلب"},
    "Innere Medizin": {"de": "Innere Medizin", "en": "Internal medicine", "fr": "Médecine interne", "ar": "الطب الباطني"},
    "Chirurgie": {"de": "Chirurgie", "en": "Surgery", "fr": "Chirurgie", "ar": "الجراحة"},
    "Onkologie": {"de": "Onkologie", "en": "Oncology", "fr": "Oncologie", "ar": "الأورام"},
    "Neurologie": {"de": "Neurologie", "en": "Neurology", "fr": "Neurologie", "ar": "الأعصاب"},
    "Endokrinologie": {"de": "Endokrinologie / Diabetologie", "en": "Endocrinology / Diabetes", "fr": "Endocrinologie / Diabétologie", "ar": "الغدد الصماء والسكري"},
    "Pneumologie": {"de": "Pneumologie", "en": "Pulmonology", "fr": "Pneumologie", "ar": "أمراض الرئة"},
    "Gastroenterologie": {"de": "Gastroenterologie", "en": "Gastroenterology", "fr": "Gastro-entérologie", "ar": "أمراض الجهاز الهضمي"},
    "Orthopädie": {"de": "Orthopädie", "en": "Orthopedics", "fr": "Orthopédie", "ar": "جراحة العظام"},
    "Psychiatrie": {"de": "Psychiatrie", "en": "Psychiatry", "fr": "Psychiatrie", "ar": "الطب النفسي"},
    "Sonstiges": {"de": "Sonstiges", "en": "Other", "fr": "Autre", "ar": "أخرى"},
}
KATEGORIEN = list(kategorie_uebersetzung)

_diagnose_klein = {k.lower(): v for k, v in diagnose_uebersetzung.items()}


def uebersetze_diagnose(text, sprache):
    """Gibt die Diagnose in der Zielsprache zurueck (unbekannte Texte bleiben unveraendert)."""
    if sprache == "de" or text is None:
        return text
    eintrag = _diagnose_klein.get(text.strip().lower())
    return eintrag[sprache] if eintrag else text


def kategorie_name(schluessel, sprache):
    """Anzeigename einer Kategorie in der Zielsprache (unbekannte Werte bleiben unveraendert)."""
    eintrag = kategorie_uebersetzung.get(schluessel)
    return eintrag[sprache] if eintrag else schluessel
