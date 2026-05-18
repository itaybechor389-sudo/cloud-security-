<div align="center">

```
╔══════════════════════════════════════════════════════════════════╗
║                   AWS-SENTINEL  v1.0                             ║
║             AWS Cloud Security Auditor                           ║
╚══════════════════════════════════════════════════════════════════╝
```

# AWS-Sentinel
### AWS Cloud Security Auditor



**A premium GUI tool for auditing AWS cloud security posture.**
Connects to a real AWS account via Access Key + Secret Key, scans IAM, S3, EC2 Security Groups, and CloudTrail — and generates a Risk Score out of 100.



</div>

---

## Real Results — Live AWS Account

This tool was tested against a real AWS account and found the following **actual vulnerabilities**:

| Finding | Severity | MITRE ATT&CK |
|---------|----------|--------------|
| S3 bucket publicly accessible to the internet | CRITICAL | T1530 |
| IAM user with console access and NO MFA | HIGH | T1078.004 |
| SSH port 22 open to 0.0.0.0/0 | CRITICAL | T1190 |
| No IAM password policy configured | CRITICAL | T1110 |
| All ports (0-65535) open to the world | CRITICAL | T1190 |

**Risk Score: 80/100 — HIGH risk environment**

---

## Features

| Tab | What it Does |
|-----|-------------|
| **>> CONNECT** | Enter AWS Access Key + Secret Key + Region |
| **>> DASHBOARD** | Threat overview, scan status, Risk Score, Run Full Audit |
| **>> IAM USERS** | MFA status, console access, access key age, groups |
| **>> S3 BUCKETS** | Public access, versioning, encryption per bucket |
| **>> SECURITY GROUPS** | Ports open to 0.0.0.0/0 (SSH, RDP, MySQL, etc.) |
| **>> SECURITY AUDIT** | Root MFA, password policy, CloudTrail, key rotation |
| **>> REPORTS** | Export HTML + JSON report with MITRE ATT&CK mapping |

---

## Installation

```bash
# 1. Install dependencies 
pip install customtkinter boto3 --break-system-packages

# 2. Run the tool
python3 aws_sentinel.py
```

---

## Usage

### Step 1 — Create AWS Access Key
```
AWS Console → IAM → Users → [your user]
→ Security credentials → Create access key
→ Local code → Create → Download .csv
```

### Step 2 — Connect
Enter in the tool:
```
ACCESS KEY ID     → AKIA...
SECRET ACCESS KEY → (your secret)
REGION            → us-east-1
```

### Step 3 — Run Full Audit
Click **>> RUN FULL AUDIT** on the Dashboard — all modules run automatically.

### Step 4 — Review Results
Check each tab for detailed findings with risk levels and recommendations.

### Step 5 — Generate Report
Click **>> REPORTS** → **>> GENERATE** → Export HTML or JSON.

---

## Security Checks

| Check | Method | What It Finds |
|-------|--------|---------------|
| **Root MFA** | IAM GetAccountSummary | Root account without MFA |
| **IAM Users MFA** | IAM ListMFADevices | Console users without MFA |
| **Password Policy** | IAM GetAccountPasswordPolicy | Missing or weak policy |
| **Access Key Age** | IAM ListAccessKeys | Keys older than 90 days |
| **S3 Public Access** | S3 GetPublicAccessBlock | Publicly accessible buckets |
| **S3 Encryption** | S3 GetBucketEncryption | Unencrypted buckets |
| **Security Groups** | EC2 DescribeSecurityGroups | Ports open to 0.0.0.0/0 |
| **CloudTrail** | CloudTrail DescribeTrails | Logging disabled |

---

## MITRE ATT&CK Mapping

| Technique ID | Name | Checked By |
|-------------|------|-----------|
| T1078 | Valid Accounts | Root account audit |
| T1078.004 | Cloud Accounts | IAM MFA check |
| T1530 | Data from Cloud Storage | S3 public access |
| T1190 | Exploit Public-Facing App | Security Groups |
| T1552.001 | Credentials in Files | Access key age |
| T1562.008 | Disable Cloud Logs | CloudTrail check |
| T1110 | Brute Force | Password policy |

---

## Tech Stack

```

```

---

## AWS Services Audited

```
IAM        — Users, Groups, Roles, Password Policy, MFA
S3         — Buckets, Public Access, Versioning, Encryption
EC2        — Security Groups, Inbound Rules
CloudTrail — Logging status, Multi-region coverage
STS        — Account identity verification
```

---


```

```

---

## Author

**Itay Bechor**

---

<div align="center">

*AWS-Sentinel v1.0 · Cyberium Academy · RTX2026 · Cloud Security NX216 Module 12*

</div>
