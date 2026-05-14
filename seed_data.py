"""Seed 5 sample regulations if the regulations table is empty."""
from datetime import date
from sqlalchemy.orm import Session
from models import Regulation, ComplianceRequirement, RegulationCategory, RiskLevel


SAMPLE_REGULATIONS = [
    {
        "title": "General Data Protection Regulation (GDPR)",
        "jurisdiction": "European Union",
        "category": RegulationCategory.GDPR,
        "summary": (
            "The GDPR is a comprehensive data protection law that governs how organizations "
            "collect, process, and store personal data of EU residents. It establishes data "
            "subject rights and imposes significant obligations on data controllers and processors."
        ),
        "full_text": (
            "Regulation (EU) 2016/679 of the European Parliament and of the Council on the "
            "protection of natural persons with regard to the processing of personal data and "
            "on the free movement of such data."
        ),
        "effective_date": date(2018, 5, 25),
        "source_url": "https://gdpr-info.eu/",
        "requirements": [
            {"text": "Obtain explicit consent before processing personal data", "risk_level": RiskLevel.critical, "category": "Consent", "mandatory": True},
            {"text": "Provide clear privacy notices to data subjects", "risk_level": RiskLevel.high, "category": "Transparency", "mandatory": True},
            {"text": "Implement the right to erasure (right to be forgotten)", "risk_level": RiskLevel.high, "category": "Data Subject Rights", "mandatory": True},
            {"text": "Report data breaches to supervisory authority within 72 hours", "risk_level": RiskLevel.critical, "category": "Breach Notification", "mandatory": True},
            {"text": "Appoint a Data Protection Officer (DPO) where required", "risk_level": RiskLevel.medium, "category": "Governance", "mandatory": False},
            {"text": "Conduct Data Protection Impact Assessments (DPIAs) for high-risk processing", "risk_level": RiskLevel.high, "category": "Risk Management", "mandatory": True},
        ],
    },
    {
        "title": "Health Insurance Portability and Accountability Act (HIPAA)",
        "jurisdiction": "United States",
        "category": RegulationCategory.HIPAA,
        "summary": (
            "HIPAA establishes national standards for the protection of sensitive patient health "
            "information (PHI). It applies to covered entities and business associates, requiring "
            "administrative, physical, and technical safeguards."
        ),
        "full_text": (
            "The Health Insurance Portability and Accountability Act of 1996 (HIPAA) and "
            "subsequent HITECH Act amendments govern the privacy and security of protected "
            "health information."
        ),
        "effective_date": date(1996, 8, 21),
        "source_url": "https://www.hhs.gov/hipaa/index.html",
        "requirements": [
            {"text": "Implement administrative safeguards including security officer designation", "risk_level": RiskLevel.critical, "category": "Administrative", "mandatory": True},
            {"text": "Establish physical safeguards for facilities and workstations", "risk_level": RiskLevel.high, "category": "Physical", "mandatory": True},
            {"text": "Deploy technical safeguards including access controls and audit logs", "risk_level": RiskLevel.critical, "category": "Technical", "mandatory": True},
            {"text": "Execute Business Associate Agreements (BAAs) with all vendors handling PHI", "risk_level": RiskLevel.critical, "category": "Contracts", "mandatory": True},
            {"text": "Conduct annual HIPAA security risk assessments", "risk_level": RiskLevel.high, "category": "Risk Management", "mandatory": True},
            {"text": "Provide HIPAA training to all workforce members", "risk_level": RiskLevel.medium, "category": "Training", "mandatory": True},
        ],
    },
    {
        "title": "Sarbanes-Oxley Act (SOX)",
        "jurisdiction": "United States",
        "category": RegulationCategory.SOX,
        "summary": (
            "SOX establishes requirements for all U.S. public company boards, management, and "
            "public accounting firms. It focuses on corporate governance, financial disclosures, "
            "and the prevention of accounting fraud."
        ),
        "full_text": (
            "The Sarbanes-Oxley Act of 2002 (Pub.L. 107-204) mandates certain practices in "
            "financial record keeping and reporting for corporations."
        ),
        "effective_date": date(2002, 7, 30),
        "source_url": "https://www.sec.gov/about/laws/soa2002.pdf",
        "requirements": [
            {"text": "CEO and CFO must certify accuracy of financial reports (Section 302)", "risk_level": RiskLevel.critical, "category": "Certification", "mandatory": True},
            {"text": "Establish and maintain internal controls over financial reporting (ICFR)", "risk_level": RiskLevel.critical, "category": "Internal Controls", "mandatory": True},
            {"text": "Maintain audit committee independence", "risk_level": RiskLevel.high, "category": "Governance", "mandatory": True},
            {"text": "Preserve all audit-related records for minimum 7 years", "risk_level": RiskLevel.high, "category": "Record Keeping", "mandatory": True},
            {"text": "Implement whistleblower protection mechanisms", "risk_level": RiskLevel.medium, "category": "Ethics", "mandatory": True},
        ],
    },
    {
        "title": "Payment Card Industry Data Security Standard (PCI DSS)",
        "jurisdiction": "Global",
        "category": RegulationCategory.PCI,
        "summary": (
            "PCI DSS is a set of security standards designed to ensure that all companies that "
            "accept, process, store, or transmit credit card information maintain a secure "
            "environment. It is administered by the PCI Security Standards Council."
        ),
        "full_text": (
            "PCI DSS v4.0 requirements cover network security, cardholder data protection, "
            "vulnerability management, access control, monitoring, and information security policies."
        ),
        "effective_date": date(2022, 3, 31),
        "source_url": "https://www.pcisecuritystandards.org/",
        "requirements": [
            {"text": "Install and maintain network security controls (firewalls)", "risk_level": RiskLevel.critical, "category": "Network Security", "mandatory": True},
            {"text": "Do not use vendor-supplied defaults for system passwords and security parameters", "risk_level": RiskLevel.critical, "category": "Configuration", "mandatory": True},
            {"text": "Protect stored cardholder data with encryption", "risk_level": RiskLevel.critical, "category": "Data Protection", "mandatory": True},
            {"text": "Encrypt transmission of cardholder data across open, public networks", "risk_level": RiskLevel.critical, "category": "Encryption", "mandatory": True},
            {"text": "Protect all systems against malware and regularly update antivirus software", "risk_level": RiskLevel.high, "category": "Vulnerability Management", "mandatory": True},
            {"text": "Restrict access to system components and cardholder data by business need to know", "risk_level": RiskLevel.high, "category": "Access Control", "mandatory": True},
            {"text": "Track and monitor all access to network resources and cardholder data", "risk_level": RiskLevel.high, "category": "Monitoring", "mandatory": True},
            {"text": "Regularly test security systems and processes", "risk_level": RiskLevel.medium, "category": "Testing", "mandatory": True},
        ],
    },
    {
        "title": "California Consumer Privacy Act (CCPA)",
        "jurisdiction": "California, United States",
        "category": RegulationCategory.CCPA,
        "summary": (
            "The CCPA grants California consumers significant privacy rights and requires "
            "businesses to disclose their data collection practices, allow consumers to opt out "
            "of the sale of their personal information, and delete consumer data upon request."
        ),
        "full_text": (
            "California Civil Code Sections 1798.100–1798.199 (CCPA) and the California Privacy "
            "Rights Act (CPRA) amendments effective January 1, 2023."
        ),
        "effective_date": date(2020, 1, 1),
        "source_url": "https://oag.ca.gov/privacy/ccpa",
        "requirements": [
            {"text": "Disclose categories of personal information collected and purpose of use", "risk_level": RiskLevel.high, "category": "Transparency", "mandatory": True},
            {"text": "Provide consumers the right to know what personal data is collected", "risk_level": RiskLevel.high, "category": "Consumer Rights", "mandatory": True},
            {"text": "Honor consumer requests to delete personal information", "risk_level": RiskLevel.high, "category": "Consumer Rights", "mandatory": True},
            {"text": "Provide opt-out mechanism for sale of personal information", "risk_level": RiskLevel.critical, "category": "Opt-Out", "mandatory": True},
            {"text": "Implement reasonable security measures to protect personal information", "risk_level": RiskLevel.high, "category": "Security", "mandatory": True},
            {"text": "Update privacy policy at least every 12 months", "risk_level": RiskLevel.medium, "category": "Documentation", "mandatory": True},
        ],
    },
]


def seed_regulations(db: Session) -> None:
    """Insert sample regulations if the table is empty."""
    existing = db.query(Regulation).count()
    if existing > 0:
        return

    print("Seeding sample regulations...")
    for reg_data in SAMPLE_REGULATIONS:
        requirements_data = reg_data.pop("requirements")
        regulation = Regulation(**reg_data)
        db.add(regulation)
        db.flush()  # get the id

        for req in requirements_data:
            db.add(ComplianceRequirement(
                regulation_id=regulation.id,
                requirement_text=req["text"],
                category=req["category"],
                risk_level=req["risk_level"],
                is_mandatory=req["mandatory"],
            ))

    db.commit()
    print(f"Seeded {len(SAMPLE_REGULATIONS)} regulations.")
