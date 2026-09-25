# Study Notes – MediLink

Study notes for the medical and technical topics behind my MediLink project.
Each file covers one topic I worked through while building the project.

| # | Topic | File |
|---|-------|------|
| 01 | Framingham Hard CHD Risk Score | [01_Framingham_Risk_Score_Notes.pdf](01_Framingham_Risk_Score_Notes.pdf) |

## 01 – Framingham Hard CHD Risk Score

**In short:** MediLink estimates a patient's 10-year risk of a heart attack or coronary death,
using age, cholesterol, blood pressure and smoking status. The formula comes from the
Framingham Heart Study, which followed thousands of people over decades.

**What I did**
- Implemented the score for men and women in `risk.py`
- Verified every coefficient against the primary source
  ([Framingham Heart Study](https://www.framinghamheartstudy.org/fhs-risk-functions/hard-coronary-heart-disease-10-year-risk/))
- Wrote automated tests for reference values, clinical rules and invalid input (`test_risk.py`)
- Added input validation, because in healthcare a wrong result is worse than no result
- Tested myself on the medical background (self-test in the PDF)

**What I learned**

<!-- Write this part yourself: 2–3 sentences in your own words.
     What did you learn? What surprised you? -->

## How these notes were made

The explanations and diagrams in the PDFs were created with AI assistance (Claude), which I used
as a tutor. The implementation, the validation against the original source and the self-tests are my own work.

> ⚠️ MediLink is a learning project. The risk calculator is a demo, not a diagnostic tool.
