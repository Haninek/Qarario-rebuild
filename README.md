Qarari Platform
Type: Flask Web Application
Purpose: Financial Risk Assessment & Loan Decision Tool powered by AI/ML
Audience: Underwriters, FinTech Firms, Lending Companies
📍Overview
The Qarari Platform is an advanced underwriting tool that helps lenders and decisionmakers assess the financial risk of applicants. It calculates a normalized risk score,
determines funding eligibility, and generates a recommendation report. The platform also
supports learning over time using machine learning to improve assessment accuracy.
📈Key Features
1. Risk Assessment Form
• Multi-step form covering:
o Personal Credit Info
o Business Info
o Bank Analysis
o Background Check
o Social Media Presence
o Capital & Collateral
o Conditions
• Smart Logic:
o Owner 2 fields hidden if Owner 1 owns 100%
o If Owner 1 < 59%, prompt user to add Owner 2
o Auto-calculates “Years in Business” from business start date
2. Scoring Engine
• Each field has a point weight defined in finance.json
• Numeric form values may be provided as strings; the scorer will
  convert them to floats when possible.
• Total score normalized to a maximum of 100
• Risk Tier displayed based on score:
  - **Low Risk** (80+)
  - **Moderate Risk** (60–79)
  - **High Risk** (50–59)
  - **Super High Risk** (<50, auto‑deny)
3. Loan Offer Generation
• Generates up to 6 dynamic offers
• Minimum offer: $5,000
• Offers based on risk tier & score
4. PDF Summary Generator
• Generates a downloadable PDF after submission
• PDF includes:
o All input fields
o Final score
o Risk tier
o Recommended offers
5. Admin & Builder Tools
• Questionnaire Builder: Add/edit/remove fields
• System Admin Panel:
o View logs
o Adjust scoring logic
o ML suggestions
• Form Preview & Testing Tools
6. Dashboard
• Main landing hub for navigation
• Should be default page (not risk form)
• Allows easy access to:
o New Assessment
o Admin Tools
o Logs & Insights
7. Machine Learning Vision (Planned)
• Logs previous risk assessments & repayment results
• Trains a model to improve:
o Scoring logic
o Offer accuracy
o Risk predictions
• Admin dashboard will suggest changes to field weights based on ML insights
💡Technical Stack
• Frontend: Bootstrap (Star Admin 2 template)
• Backend: Python Flask
• PDF Gen: pdfkit or WeasyPrint
• ML (Optional): Scikit-learn
• Storage: Local file logging or JSON (upgradeable to DB)
✅Completion Checklist
Feature Status Notes
100pt Normalized Score Logic from finance.json
Conditional Owner 2 Logic Works dynamically
Auto Years in Business Fills from start date
Offer Generation (min $5k) Up to 6 offers shown
Super High Risk Rejection No offer shown
PDF Summary Includes inputs, score, tier
Dashboard Default View Routing issue, needs fixing
Admin Tools Works partially, needs polish
ML Integration Conceptual, not trained yet
🚀How to Use
1. Launch the Flask app.
2. Navigate to the Dashboard.
3. Click “Start New Assessment.”
4. Complete the form.
5. View result, score, and offers.
6. Download the PDF.
7. For admins, visit builder/tools.
