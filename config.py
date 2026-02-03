REPORT_CONFIG = {
  "meta": {
    "title": "UCP Compliance Audit Report",
    "subtitle": "Universal Content Protocol Technical Assessment",
    "generatorName": "UCP Compliance Scanner",
    "version": "2.4"
  },
  "labels": {
    "reviewDate": "Review date",
    "siteReviewed": "Site reviewed",
    "scoreTitle": "Weighted compliance score",
    "breakdownTitle": "Detailed component breakdown",
    "methodologyTitle": "Scoring methodology",
    "privacyTitle": "Privacy & data protection notice",
    "tableHeaders": {
      "component": "Component",
      "weight": "Weight",
      "score": "Score",
      "status": "Status"
    }
  },
  "ui": {
    "theme": {
      "primary": "#667eea",
      "secondary": "#764ba2",
      "ok": "#10b981",
      "warn": "#f59e0b",
      "bad": "#ef4444",
      "text": "#111827",
      "muted": "#6b7280",
      "border": "#e5e7eb",
      "bgSoft": "#f9fafb"
    }
  },
  "scoring": {
    "weights": {
      "robots": 20,
      "ucpConfig": 50,
      "headers": 30
    },
    "thresholds": {
      "compliantMin": 70,
      "partialMin": 50
    },
    "penalties": {
      "ucpInvalidJson": 10
    },
    "labels": {
      "compliant": "UCP COMPLIANT",
      "partial": "PARTIALLY COMPLIANT",
      "non": "NON-COMPLIANT"
    },
    "componentsCopy": {
      "robots": "Presence of UCP references in robots.txt",
      "ucpConfig": "Accessibility and format of /.well-known/ucp",
      "headers": "Presence of UCP-related headers in HTTP response"
    }
  },
  "disclaimer": {
    "title": "Privacy & data protection notice",
    "reviewerLocation": "Netherlands (EU)",
    "paragraphs": [
      "GDPR alignment: This automated technical assessment is designed to follow data minimization and purpose limitation principles.",
      "No data storage: The service is intended to run with zero data retention (in-memory processing only) and does not store site content or results after the PDF is generated.",
      "Automated processing: The scan is fully automated and checks only publicly accessible endpoints (robots.txt, /.well-known/ucp, HTTP headers).",
      "Informational use: This report is provided for informational purposes and should be complemented with your own validation."
    ],
    "crossBorderTemplateUS": "Cross-border note: This assessment is executed from the Netherlands (EU) while reviewing a US-facing site. The scan is limited to public technical endpoints and performed in a compliance-oriented manner.",
    "crossBorderTemplateGeneric": "Cross-border note: This assessment is executed from the Netherlands (EU) while reviewing websites hosted in other jurisdictions. The scan is limited to public technical endpoints and performed in a compliance-oriented manner."
  }
}
