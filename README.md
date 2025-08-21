
# Qarari Platform

**Type:** Flask Web Application  
**Purpose:** Advanced Financial Risk Assessment & Loan Decision Platform powered by AI/ML  
**Audience:** Underwriters, FinTech Firms, Lending Companies, API Developers

## 📍 Overview

The Qarari Platform is a comprehensive underwriting solution that helps lenders assess financial risk with precision. It combines traditional risk assessment with machine learning capabilities, offers API integration, and provides advanced admin tools for customization and model management.

## 🚀 Key Features

### 1. Risk Assessment Engine
- **Multi-step Assessment Form** covering:
  - Personal Credit Information
  - Business Information & Analytics
  - Bank Account Analysis
  - Background Verification
  - Social Media & Digital Presence
  - Capital & Collateral Assessment
  - Market Conditions Analysis
- **Smart Conditional Logic:**
  - Owner 2 fields appear/hide based on Owner 1 ownership percentage
  - Auto-calculates "Years in Business" from start date
  - Dynamic field validation and requirements

### 2. Advanced Scoring System
- **100-Point Normalized Scoring** from configurable rules (finance.json)
- **Risk Classification Tiers:**
  - 🟢 **Low Risk** (80+): Premium rates, high funding amounts
  - 🟡 **Moderate Risk** (70-79): Standard rates and terms
  - 🟠 **High Risk** (60-69): Higher rates, reduced amounts
  - 🔴 **Super High Risk** (50-59): Maximum rates, minimal amounts
  - ❌ **Auto-Deny** (<50): No funding offers
- **Weighted Factor Scoring** with customizable field weights

### 3. Dynamic Loan Offer Generation
- Up to 6 tailored offers per assessment
- Risk-based pricing with factor rates from 73% to 292% APR
- Flexible terms: 30-180 days based on risk tier
- Minimum offer amount: $5,000
- Maximum offers up to $500,000 for low-risk applicants

### 4. Professional PDF Reports
- Credit report-style formatting with colors and branding
- Comprehensive risk breakdown with weighted factors
- All input data, scores, and recommendations
- Downloadable summary for client records

### 5. REST API Integration
- **Authentication:** API key + token based security
- **Sandbox Mode:** Testing environment for development
- **Pay-per-Call Pricing:** $1.25 per API assessment
- **Enterprise Support:** Dedicated sales consultation
- **JSON Responses:** Structured data for easy integration
- **Rate Limiting:** Built-in usage monitoring and controls

### 6. Machine Learning Platform
- **Model Training Interface:** Train custom risk models
- **Multiple Algorithms:** Logistic Regression, Random Forest, Neural Networks
- **Hyperparameter Tuning:** Automated optimization
- **Model Management:** Deploy, monitor, and update models
- **Training Job Monitoring:** Real-time progress tracking
- **Performance Metrics:** Accuracy, loss, and validation tracking

### 7. User Management System
- **Role-Based Access Control:** Admin, User, API-Only users
- **Subscription Management:** Different tiers and API access levels
- **API Credential Management:** Secure key generation and rotation
- **Usage Tracking:** API call monitoring and billing
- **Dashboard Customization:** Personalized user interfaces

### 8. Admin & Configuration Tools
- **Questionnaire Builder:** Dynamic form field management
- **Scoring Rule Editor:** Real-time weight and logic adjustments
- **System Monitoring:** Logs, status, and performance metrics
- **ML Model Management:** Deploy and manage trained models
- **User Administration:** Manage accounts, subscriptions, and permissions

### 9. Advanced Analytics
- **Underwriting Insights:** Historical data analysis
- **Risk Pattern Recognition:** ML-powered trend analysis
- **Performance Dashboards:** Real-time system metrics
- **Decision Logging:** Complete audit trail of all assessments

## 💻 Technical Architecture

- **Backend:** Python Flask with modular blueprint structure
- **Frontend:** Bootstrap 5 with Star Admin template
- **Authentication:** Token-based API auth + session management
- **PDF Generation:** Enhanced reporting with professional styling
- **ML Framework:** Scikit-learn integration for model training
- **Data Storage:** JSON-based with upgrade path to databases
- **API Design:** RESTful endpoints with comprehensive documentation

## 🔧 API Endpoints

### Assessment Endpoints
- `POST /api/score` - Submit risk assessment
- `GET /api/offers/{assessment_id}` - Retrieve loan offers
- `GET /api/status/{job_id}` - Check assessment status

### Model Management
- `POST /api/models/train` - Start model training
- `GET /api/models` - List available models
- `POST /api/models/deploy` - Deploy trained model

### User Management
- `POST /api/auth/token` - Generate API token
- `GET /api/usage` - Check API usage statistics
- `POST /api/sandbox` - Sandbox testing mode

## 📋 Risk Assessment Categories

### Personal Credit (Weight: 26)
- Credit Score, Inquiries, Utilization, Past Due Accounts
- Dual owner support with conditional logic

### Business Intelligence (Weight: 19)
- Intelliscore, Stability Score, Years in Business, Inquiries

### Banking Analysis (Weight: 30)
- Daily Average Balance, Monthly Deposits, NSF Count
- Negative Days, Deposit Frequency Analysis

### Verification & Background (Weight: 15)
- Criminal Background, Judgments, UCC Filings
- Contact Verification, Digital Presence

### Collateral & Assets (Weight: 6)
- Business Assets, Asset Valuation
- Location Quality, Distance Analysis

### Market Conditions (Weight: 4)
- Industry Type, Loan Purpose, Requested Amount
- Underwriter Adjustment Factor

## 🚀 Getting Started

1. **Start the Application:**
   ```bash
   python main.py
   ```
   
2. **Access the Dashboard:**
   Navigate to `http://localhost:5000`

3. **Create Assessment:**
   - Click "Start New Assessment"
   - Complete the multi-step form
   - Review scoring and offers
   - Download PDF report

4. **API Integration:**
   - Register for API access
   - Generate API credentials
   - Use sandbox mode for testing
   - Implement production endpoints

5. **Admin Configuration:**
   - Access `/admin` for system management
   - Use `/builder` for questionnaire customization
   - Train ML models via `/ml/train`

## 📊 Pricing Structure

- **Dashboard Access:** Free for registered users
- **API Calls:** $1.25 per assessment
- **Sandbox Mode:** Unlimited testing for development
- **Enterprise:** Custom pricing with dedicated support

## 🔒 Security Features

- API key authentication with token rotation
- Role-based access control
- Secure credential storage
- Rate limiting and usage monitoring
- Audit logging for compliance

## 📈 ML & Analytics

- **Model Training:** Custom algorithms for risk prediction
- **Performance Tracking:** Real-time accuracy monitoring
- **A/B Testing:** Compare model performance
- **Feature Importance:** Understand key risk factors
- **Automated Retraining:** Keep models current

## 🛠️ Customization Options

- **Field Weights:** Adjust scoring importance via JSON config
- **Risk Tiers:** Modify thresholds and rate structures
- **Offer Logic:** Customize funding amounts and terms
- **Form Fields:** Add, remove, or modify assessment questions
- **Branding:** Customize PDF reports and UI themes

## 📞 Support & Documentation

- **API Documentation:** Comprehensive endpoint guide at `/api/docs`
- **User Guides:** Built-in help and tutorials
- **Enterprise Support:** Dedicated account management
- **Developer Resources:** Code examples and integration guides

---

**Version:** 2.0  
**Last Updated:** January 2024  
**License:** Proprietary - Contact for licensing information
