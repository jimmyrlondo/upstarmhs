#!/usr/bin/env python3
"""
Upstar MHS API Server
Email routing:
  - Start Services referral  -> ADMIN_EMAIL + INTAKE_EMAIL
  - Careers application      -> ADMIN_EMAIL only
  - Contact form             -> ADMIN_EMAIL only
"""

import asyncio
import json
import subprocess
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Upstar MHS Referral API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ADMIN_EMAIL  = "a.nicole@upstarmhs.com"   # receives ALL form submissions
INTAKE_EMAIL = "s.hairston@upstarmhs.com"  # also receives Start Services referrals
INFO_EMAIL   = "info@upstarmhs.com"


async def call_tool(source_id: str, tool_name: str, arguments: dict) -> dict:
    """Call an external tool via the external-tool CLI."""
    payload = json.dumps({
        "source_id": source_id,
        "tool_name": tool_name,
        "arguments": arguments,
    })
    proc = await asyncio.create_subprocess_exec(
        "external-tool", "call", payload,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"Tool call failed: {stderr.decode()}")
    return json.loads(stdout.decode())


class Form1Data(BaseModel):
    referral_type: str  # 'child' or 'adult'
    # Child fields
    child_name: Optional[str] = ""
    child_dob: Optional[str] = ""
    child_age: Optional[str] = ""
    child_race: Optional[str] = ""
    child_address: Optional[str] = ""
    guardian_name: Optional[str] = ""
    guardian_phone: Optional[str] = ""
    guardian_email: Optional[str] = ""
    guardian_relationship: Optional[str] = ""
    # Adult fields
    adult_name: Optional[str] = ""
    adult_dob: Optional[str] = ""
    adult_age: Optional[str] = ""
    adult_race: Optional[str] = ""
    adult_address: Optional[str] = ""
    adult_phone: Optional[str] = ""
    adult_email: Optional[str] = ""
    # Shared fields
    insurance_company: str
    medicaid_number: str
    member_id: str
    referring_source: str
    referring_source_name: Optional[str] = ""


class Form2Data(BaseModel):
    full_name: str
    dob: str
    ssn: str
    medicaid: str
    member_id: Optional[str] = ""
    gender: Optional[str] = ""
    marital_status: Optional[str] = ""
    race: Optional[str] = ""


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Upstar MHS Referral API"}


@app.post("/api/referral")
async def submit_referral(data: Form1Data):
    """
    Handles Form 1 (referral info). Sends email to admin with
    all referral details and a link to the Step 2 Google Form.
    """
    ref_source_line = data.referring_source
    if data.referring_source_name:
        ref_source_line += f" ({data.referring_source_name})"

    is_child = data.referral_type == 'child'
    display_name = data.child_name if is_child else data.adult_name
    referral_label = "Child Referral" if is_child else "Adult Referral"

    if is_child:
        participant_block = f"""Child Information:
Name: {data.child_name}
Date of Birth: {data.child_dob}
Age: {data.child_age}
Race: {data.child_race}
Address: {data.child_address}

Parent / Guardian:
Name: {data.guardian_name}
Relationship: {data.guardian_relationship}
Phone: {data.guardian_phone}
Email: {data.guardian_email}"""
        participant_html = f"""
    <h2 style="color:#2d3047;font-size:16px;margin:0 0 12px">Child Information</h2>
    <table style="width:100%;border-collapse:collapse;font-size:14px">
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:7px 0;color:#666;width:160px">Name</td><td style="padding:7px 0;font-weight:600">{data.child_name}</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:7px 0;color:#666">Date of Birth</td><td style="padding:7px 0">{data.child_dob}</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:7px 0;color:#666">Age</td><td style="padding:7px 0">{data.child_age}</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:7px 0;color:#666">Race</td><td style="padding:7px 0">{data.child_race}</td></tr>
      <tr><td style="padding:7px 0;color:#666">Address</td><td style="padding:7px 0">{data.child_address}</td></tr>
    </table>
    <h2 style="color:#2d3047;font-size:16px;margin:20px 0 12px">Parent / Guardian</h2>
    <table style="width:100%;border-collapse:collapse;font-size:14px">
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:7px 0;color:#666;width:160px">Name</td><td style="padding:7px 0;font-weight:600">{data.guardian_name}</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:7px 0;color:#666">Relationship</td><td style="padding:7px 0">{data.guardian_relationship}</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:7px 0;color:#666">Phone</td><td style="padding:7px 0">{data.guardian_phone}</td></tr>
      <tr><td style="padding:7px 0;color:#666">Email</td><td style="padding:7px 0">{data.guardian_email}</td></tr>
    </table>"""
    else:
        participant_block = f"""Adult Information:
Name: {data.adult_name}
Date of Birth: {data.adult_dob}
Age: {data.adult_age}
Race: {data.adult_race}
Address: {data.adult_address}
Phone: {data.adult_phone}
Email: {data.adult_email}"""
        participant_html = f"""
    <h2 style="color:#2d3047;font-size:16px;margin:0 0 12px">Adult Information</h2>
    <table style="width:100%;border-collapse:collapse;font-size:14px">
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:7px 0;color:#666;width:160px">Name</td><td style="padding:7px 0;font-weight:600">{data.adult_name}</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:7px 0;color:#666">Date of Birth</td><td style="padding:7px 0">{data.adult_dob}</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:7px 0;color:#666">Age</td><td style="padding:7px 0">{data.adult_age}</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:7px 0;color:#666">Race</td><td style="padding:7px 0">{data.adult_race}</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:7px 0;color:#666">Address</td><td style="padding:7px 0">{data.adult_address}</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:7px 0;color:#666">Phone</td><td style="padding:7px 0">{data.adult_phone}</td></tr>
      <tr><td style="padding:7px 0;color:#666">Email</td><td style="padding:7px 0">{data.adult_email}</td></tr>
    </table>"""

    plain_body = f"""New Referral Received - {referral_label}

{participant_block}

Insurance:
Insurance Company: {data.insurance_company}
Medicaid #: {data.medicaid_number}
Member ID: {data.member_id}

Referring Source: {ref_source_line}

Submitted via the Upstar MHS website.
"""

    html_body = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
  <div style="background: #2d3047; padding: 24px 28px; border-radius: 8px 8px 0 0;">
    <h1 style="color: #eec643; margin: 0; font-size: 20px;">UPSTAR Mental Health Services</h1>
    <p style="color: rgba(255,255,255,0.7); margin: 4px 0 0; font-size: 14px;">New {referral_label} Submitted</p>
  </div>
  <div style="background: #fff; padding: 28px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
    {participant_html}
    <h2 style="color: #2d3047; font-size: 16px; margin: 20px 0 12px;">Insurance</h2>
    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:7px 0;color:#666;width:160px">Insurance Company</td><td style="padding:7px 0;font-weight:600">{data.insurance_company}</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:7px 0;color:#666">Medicaid #</td><td style="padding:7px 0;font-weight:600">{data.medicaid_number}</td></tr>
      <tr><td style="padding:7px 0;color:#666">Member ID</td><td style="padding:7px 0">{data.member_id}</td></tr>
    </table>
    <h2 style="color: #2d3047; font-size: 16px; margin: 20px 0 12px;">Referring Source</h2>
    <p style="font-size:14px;background:#f9fafb;padding:12px 16px;border-radius:6px;border-left:3px solid #1b998b;margin:0">{ref_source_line}</p>
    <p style="font-size: 12px; color: #9ca3af; margin: 24px 0 0;">Submitted via Upstar MHS website referral form</p>
  </div>
</div>
"""

    await call_tool("gcal", "send_email", {
        "action": {
            "action": "send",
            "to": [ADMIN_EMAIL, INTAKE_EMAIL],
            "cc": [],
            "bcc": [],
            "subject": f"New {referral_label}: {display_name}",
            "body": plain_body,
            "html_body": html_body
        }
    })

    return {"success": True, "message": "Referral submitted successfully."}


@app.post("/api/referral-step2")
async def submit_referral_step2(data: Form2Data):
    """
    Handles Form 2 (secure/sensitive info). Sends a confidential email
    to admin with the full secure intake data.
    """
    plain_body = f"""Secure Intake Received - Step 2 Complete

Participant: {data.full_name}
Date of Birth: {data.dob}
SSN: {data.ssn}
Medicaid Number (MMIS): {data.medicaid}
Member ID: {data.member_id or 'N/A'}
Gender: {data.gender or 'N/A'}
Marital Status: {data.marital_status or 'N/A'}
Race / Ethnicity: {data.race or 'N/A'}

This is confidential information submitted via the Upstar MHS secure intake form.
"""

    html_body = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
  <div style="background: #1a2e4a; padding: 24px 28px; border-radius: 8px 8px 0 0;">
    <h1 style="color: #f5b800; margin: 0; font-size: 20px;">UPSTAR Mental Health</h1>
    <p style="color: rgba(255,255,255,0.7); margin: 4px 0 0; font-size: 14px;">Secure Intake - Step 2 Submitted</p>
  </div>
  <div style="background: #fff; padding: 28px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">

    <div style="background: #fef9c3; border: 1px solid #fde047; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px;">
      <p style="margin: 0; font-size: 13px; color: #713f12; font-weight: 600;">Confidential - Handle per HIPAA guidelines</p>
    </div>

    <h2 style="color: #1a2e4a; font-size: 16px; margin: 0 0 16px;">Secure Intake Details</h2>
    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
      <tr style="border-bottom: 1px solid #f3f4f6;"><td style="padding: 8px 0; color: #666; width: 160px;">Participant Name</td><td style="padding: 8px 0; font-weight: 600;">{data.full_name}</td></tr>
      <tr style="border-bottom: 1px solid #f3f4f6;"><td style="padding: 8px 0; color: #666;">Date of Birth</td><td style="padding: 8px 0;">{data.dob}</td></tr>
      <tr style="border-bottom: 1px solid #f3f4f6;"><td style="padding: 8px 0; color: #666;">Social Security #</td><td style="padding: 8px 0;">{data.ssn}</td></tr>
      <tr style="border-bottom: 1px solid #f3f4f6;"><td style="padding: 8px 0; color: #666;">Medicaid # (MMIS)</td><td style="padding: 8px 0; font-weight: 600;">{data.medicaid}</td></tr>
      <tr style="border-bottom: 1px solid #f3f4f6;"><td style="padding: 8px 0; color: #666;">Member ID</td><td style="padding: 8px 0;">{data.member_id or 'N/A'}</td></tr>
      <tr style="border-bottom: 1px solid #f3f4f6;"><td style="padding: 8px 0; color: #666;">Gender</td><td style="padding: 8px 0;">{data.gender or 'N/A'}</td></tr>
      <tr style="border-bottom: 1px solid #f3f4f6;"><td style="padding: 8px 0; color: #666;">Marital Status</td><td style="padding: 8px 0;">{data.marital_status or 'N/A'}</td></tr>
      <tr><td style="padding: 8px 0; color: #666;">Race / Ethnicity</td><td style="padding: 8px 0;">{data.race or 'N/A'}</td></tr>
    </table>

    <p style="font-size: 12px; color: #9ca3af; margin: 24px 0 0;">Submitted via Upstar MHS secure intake form (Step 2)</p>
  </div>
</div>
"""

    await call_tool("gcal", "send_email", {
        "action": {
            "action": "send",
            "to": [ADMIN_EMAIL],
            "cc": [],
            "bcc": [],
            "subject": f"CONFIDENTIAL: Secure Intake - {data.full_name} (Step 2)",
            "body": plain_body,
            "html_body": html_body
        }
    })

    return {"success": True, "message": "Secure intake submitted successfully."}


@app.post("/api/contact")
async def submit_contact(request: Request):
    """Handles general contact form. Sends to ADMIN_EMAIL only."""
    data = await request.json()
    name    = data.get("name", "").strip()
    email   = data.get("email", "").strip()
    phone   = data.get("phone", "").strip()
    subject = data.get("subject", "").strip()
    message = data.get("message", "").strip()

    plain_body = f"""New Contact Form Message

From: {name}
Email: {email}
Phone: {phone or 'N/A'}
Subject: {subject or 'N/A'}

Message:
{message}

Submitted via Upstar MHS website contact form.
"""

    html_body = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
  <div style="background: #2d3047; padding: 24px 28px; border-radius: 8px 8px 0 0;">
    <h1 style="color: #eec643; margin: 0; font-size: 20px;">UPSTAR Mental Health Services</h1>
    <p style="color: rgba(255,255,255,0.7); margin: 4px 0 0; font-size: 14px;">New Contact Form Message</p>
  </div>
  <div style="background: #fff; padding: 28px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:7px 0;color:#666;width:120px">Name</td><td style="padding:7px 0;font-weight:600">{name}</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:7px 0;color:#666">Email</td><td style="padding:7px 0">{email}</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:7px 0;color:#666">Phone</td><td style="padding:7px 0">{phone or 'N/A'}</td></tr>
      <tr><td style="padding:7px 0;color:#666">Subject</td><td style="padding:7px 0">{subject or 'N/A'}</td></tr>
    </table>
    <h2 style="color: #2d3047; font-size: 16px; margin: 20px 0 12px;">Message</h2>
    <p style="font-size:14px;background:#f9fafb;padding:12px 16px;border-radius:6px;border-left:3px solid #ff8552;margin:0">{message}</p>
    <p style="font-size: 12px; color: #9ca3af; margin: 24px 0 0;">Submitted via Upstar MHS website contact form</p>
  </div>
</div>
"""

    await call_tool("gcal", "send_email", {
        "action": {
            "action": "send",
            "to": [ADMIN_EMAIL],
            "cc": [],
            "bcc": [],
            "subject": f"Website Message: {name} - {subject or 'General Inquiry'}",
            "body": plain_body,
            "html_body": html_body
        }
    })

    return {"success": True, "message": "Message sent successfully."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


class ApplyData(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    city: str
    position: str
    licensure: Optional[str] = ""
    experience: Optional[str] = ""
    why: str
    availability: Optional[str] = ""


@app.post("/api/apply")
async def submit_application(data: ApplyData):
    """Handles job application form submissions."""
    full_name = f"{data.first_name} {data.last_name}"

    plain_body = f"""New Job Application Received

Position: {data.position}
Name: {full_name}
Email: {data.email}
Phone: {data.phone}
City / Region: {data.city}
Licensure: {data.licensure or 'N/A'}
Experience: {data.experience or 'N/A'}
Availability: {data.availability or 'N/A'}

Why They Want to Join Upstar:
{data.why}

Submitted via Upstar MHS Careers page.
"""

    html_body = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
  <div style="background: #2d3047; padding: 24px 28px; border-radius: 8px 8px 0 0;">
    <h1 style="color: #eec643; margin: 0; font-size: 20px;">UPSTAR Mental Health</h1>
    <p style="color: rgba(255,255,255,0.7); margin: 4px 0 0; font-size: 14px;">New Job Application</p>
  </div>
  <div style="background: #fff; padding: 28px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
    <div style="background: #e6fafc; border: 1px solid #1b998b; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px;">
      <p style="margin: 0; font-weight: 700; color: #1b998b; font-size: 15px;">Position: {data.position}</p>
    </div>
    <h2 style="color: #2d3047; font-size: 16px; margin: 0 0 16px;">Applicant Details</h2>
    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:8px 0;color:#666;width:140px">Name</td><td style="padding:8px 0;font-weight:600">{full_name}</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:8px 0;color:#666">Email</td><td style="padding:8px 0">{data.email}</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:8px 0;color:#666">Phone</td><td style="padding:8px 0">{data.phone}</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:8px 0;color:#666">City / Region</td><td style="padding:8px 0">{data.city}</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:8px 0;color:#666">Licensure</td><td style="padding:8px 0">{data.licensure or 'N/A'}</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:8px 0;color:#666">Experience</td><td style="padding:8px 0">{data.experience or 'N/A'}</td></tr>
      <tr><td style="padding:8px 0;color:#666">Availability</td><td style="padding:8px 0">{data.availability or 'N/A'}</td></tr>
    </table>
    <h2 style="color: #2d3047; font-size: 16px; margin: 20px 0 12px;">Why They Want to Join Upstar</h2>
    <p style="font-size:14px;background:#f9fafb;padding:12px 16px;border-radius:6px;border-left:3px solid #1b998b;margin:0">{data.why}</p>
    <p style="font-size:12px;color:#9ca3af;margin:20px 0 0">Submitted via Upstar MHS Careers page</p>
  </div>
</div>
"""

    await call_tool("gcal", "send_email", {
        "action": {
            "action": "send",
            "to": [ADMIN_EMAIL],
            "cc": [],
            "bcc": [],
            "subject": f"New Application: {data.position} - {full_name}",
            "body": plain_body,
            "html_body": html_body
        }
    })

    return {"success": True, "message": "Application submitted successfully."}
