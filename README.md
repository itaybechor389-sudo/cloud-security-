<div align="center">

# 🔐 AWS-Sentinel
### AWS Cloud Security Auditor



**A GUI tool for auditing AWS cloud security posture.**
Connects to a real AWS account via API keys, scans IAM · S3 · EC2 · CloudTrail, and generates a Risk Score out of 100.

</div>

---

## 🎯 Overview

AWS-Sentinel is a security auditing tool that connects to your AWS account using Access Key credentials and performs automated security checks across multiple AWS services. It identifies misconfigurations, weak policies, and exposed resources — then calculates a Risk Score to quantify the overall security posture.

---

## ✅ Real Results

Tested against a live AWS account and found real vulnerabilities:

| 🔴 Finding | Severity | MITRE ID |
|-----------|----------|----------|
| S3 bucket publicly accessible | CRITICAL | T1530 |
| IAM user with console access and no MFA | HIGH | T1078.004 |
| SSH (port 22) open to 0.0.0.0/0 | CRITICAL | T1190 |
| No IAM password policy configured | CRITICAL | T1110 |
| All ports (0-65535) open to the world | CRITICAL | T1190 |

> **🔴 Risk Score: 80 / 100 — HIGH risk environment**

---

## 🖥️ Features

| Tab | Description |
|-----|-------------|
| 🔑 **Connect** | Enter AWS Access Key + Secret Key + Region |
| 📊 **Dashboard** | Threat overview, scan status, Risk Score, Run Full Audit |
| 👤 **IAM Users** | MFA status, console access, access key age, group membership |
| 🪣 **S3 Buckets** | Public access, versioning, encryption per bucket |
| 🔒 **Security Groups** | Dangerous ports open to 0.0.0.0/0 |
| ⚠️ **Security Audit** | Root MFA, password policy, CloudTrail, key rotation |
| 📄 **Reports** | Export full HTML + JSON report with MITRE ATT&CK mapping |

---

## ⚡ Installation

```bash
# Install dependencies
pip install customtkinter boto3 --break-system-packages

# Run
python3 aws_sentinel.py
```

---

## 🚀 Usage

### 1️⃣ Create AWS Access Key
```
AWS Console → IAM → Users → [your user]
→ Security credentials → Create access key
→ Local code → Create → Download .csv
```

### 2️⃣ Connect the Tool
```
ACCESS KEY ID     → AKIA...
SECRET ACCESS KEY → your secret
REGION            → us-east-1
```

### 3️⃣ Run Full Audit
Click **▶ RUN FULL AUDIT** — all modules run automatically and results appear in each tab.

### 4️⃣ Generate Report
Go to **Reports** tab → click **Generate** → export as HTML or JSON.

---

## 🔍 Security Checks

| ✅ Check | Method | What It Finds |
|---------|--------|---------------|
| Root MFA | IAM GetAccountSummary | Root without MFA |
| IAM MFA | IAM ListMFADevices | Console users without MFA |
| Password Policy | IAM GetAccountPasswordPolicy | Missing or weak policy |
| Access Key Age | IAM ListAccessKeys | Keys older than 90 days |
| S3 Public Access | S3 GetPublicAccessBlock | Publicly accessible buckets |
| S3 Encryption | S3 GetBucketEncryption | Unencrypted buckets |
| Security Groups | EC2 DescribeSecurityGroups | Ports open to 0.0.0.0/0 |
| CloudTrail | CloudTrail DescribeTrails | Logging disabled |

---

## 🗺️ MITRE ATT&CK Mapping

| ID | Technique | Covered By |
|----|-----------|-----------|
| T1078 | Valid Accounts | Root account audit |
| T1078.004 | Cloud Accounts | IAM MFA check |
| T1530 | Data from Cloud Storage | S3 public access scan |
| T1190 | Exploit Public-Facing App | Security Groups scan |
| T1552.001 | Credentials in Files | Access key age check |
| T1562.008 | Disable Cloud Logs | CloudTrail audit |
| T1110 | Brute Force | Password policy check |

---

## 🛠️ Tech Stack

```
Python 3.x
├── 🎨 customtkinter   — Premium dark GUI (orange/black AWS theme)
├── ☁️  boto3           — AWS SDK (IAM, S3, EC2, CloudTrail, STS)
├── 📊 tkinter ttk     — Treeview data tables
└── 🔄 threading       — Non-blocking async scans
```

---

## ☁️ AWS Services Audited

```
🔑 IAM        → Users, MFA, Password Policy, Access Keys
🪣 S3         → Public Access, Versioning, Encryption
🔒 EC2        → Security Groups, Inbound Rules
📋 CloudTrail → Logging status, Multi-region
🆔 STS        → Account identity verification
```

---

## 📁 Project Structure

```
aws-sentinel/
├── 🐍 aws_sentinel.py   — Main application
└── 📖 README.md         — Documentation
```

---

## 👨‍💻 Author

**Itay Bechor**


---

<div align="center">

⭐ **Star this repo if you found it useful!**

*AWS-Sentinel v1.0 · Built with Python + boto3*

</div>
