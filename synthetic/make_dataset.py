"""Builds the SYNTHETIC stand-in HRD corpus and the query set.

The real HRD documents are confidential and were not shared, so every fact
below is invented. Replace corpus.jsonl / queries.jsonl with real data using
the same fields and the benchmark runs unchanged.

Run:  python make_dataset.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent

DOCS = [
    ("HRD-POL-001", "Annual Leave Policy", [
        ("1 Purpose and Scope",
         "This policy sets out annual leave rules for full-time and part-time staff who have "
         "completed probation. Interns are not covered by this policy; their time off is described "
         "in the Intern Handbook (HRD-HB-006). Sick leave and special leave are covered separately "
         "in HRD-POL-002."),
        ("2 Entitlement",
         "Full-time staff are entitled to 18 working days of paid annual leave per calendar year, "
         "accrued at 1.5 days per month. Part-time staff receive a pro-rata entitlement based on "
         "contracted hours. After five full years of service the entitlement rises to 21 working days."),
        ("3 Requesting Leave",
         "Leave requests are submitted in the HRIS. Requests for three or more consecutive days must "
         "be submitted at least 10 working days in advance; shorter absences need 2 working days of "
         "notice. The line manager approves or declines within 3 working days of the request."),
        ("4 Carry-over and Payout",
         "A maximum of 5 unused annual leave days may be carried over to the next year. Carried-over "
         "days must be used by 31 March or they are forfeited. Unused annual leave is not paid out in "
         "cash, except for accrued days outstanding when employment ends."),
        ("5 Public Holidays and Blackout Periods",
         "Public holidays that fall inside a period of annual leave are not deducted from the leave "
         "balance. The Finance team has a blackout period during the last two weeks of the fiscal "
         "year, when annual leave is approved only in exceptional circumstances."),
    ]),
    ("HRD-POL-002", "Sick and Special Leave Policy", [
        ("1 Scope",
         "This policy covers sick leave and special leave for all confirmed staff and staff on "
         "probation. Annual leave is governed by HRD-POL-001."),
        ("2 Sick Leave Entitlement",
         "Staff receive 12 paid sick days per calendar year. The employee must notify the line manager "
         "before 9:00 on the first day of absence. A medical certificate is required for any absence "
         "longer than 2 consecutive days and must be uploaded to the HRIS within 3 working days of "
         "returning."),
        ("3 Extended Illness",
         "When the 12 paid sick days are used up, HRD may approve extended sick leave of up to 60 "
         "days at half pay. Approval requires a written report from the treating doctor and is "
         "reviewed every 30 days."),
        ("4 Special Leave",
         "Paid special leave is granted for the following events: the employee's own marriage, 3 days; "
         "bereavement of an immediate family member, 5 days; paternity, 10 days; maternity, 90 days. "
         "Special leave is separate from the annual leave balance."),
        ("5 Carry-over",
         "Unused sick leave does not carry over to the following year and is never paid out, "
         "including when employment ends."),
    ]),
    ("HRD-POL-003", "Training and Development Policy", [
        ("1 Purpose",
         "The organisation invests in the professional development of its staff. This policy explains "
         "the training budget, how training is approved, and the obligations that come with funded "
         "courses."),
        ("2 Annual Training Budget",
         "Each confirmed employee has a training budget of USD 600 per fiscal year. Unused budget does "
         "not roll over. Requests above USD 600 require approval from both the department head and "
         "the HRD director."),
        ("3 Approval Workflow",
         "The employee submits Training Request Form TR-2 at least 15 working days before the course "
         "start date. HRD responds within 5 working days. Courses booked without an approved TR-2 are "
         "not reimbursed."),
        ("4 Training Bond",
         "Any single course costing more than USD 1,500 requires a 12-month service agreement signed "
         "before enrolment. An employee who resigns within the 12 months repays the course fee on a "
         "pro-rata basis for the months not served."),
        ("5 Mandatory Training",
         "All staff complete information security awareness training every year by 30 June. New "
         "joiners complete code of conduct training within 30 days of their start date. Completion is "
         "tracked in the HRIS."),
        ("6 Evaluation",
         "Within 10 working days of finishing a funded course the employee submits a post-training "
         "report to the line manager and uploads any certificate to the HRIS."),
    ]),
    ("HRD-PRO-004", "Performance Review Procedure", [
        ("1 Review Cycle",
         "Performance is reviewed twice a year: a mid-year review in July and a year-end review in "
         "January. Each review consists of a self-assessment, a manager assessment and a one-to-one "
         "meeting."),
        ("2 Rating Scale",
         "Managers assign an overall rating from 1 to 5: 1 Unsatisfactory, 2 Needs improvement, "
         "3 Meets expectations, 4 Exceeds expectations, 5 Outstanding. A rating of 2 or below starts a "
         "performance improvement plan."),
        ("3 Performance Improvement Plan",
         "A performance improvement plan runs for 90 days with written objectives agreed by the "
         "employee, the manager and HRD. Progress check-ins are held every 30 days and recorded in "
         "the HRIS."),
        ("4 Calibration and Appeals",
         "Ratings are calibrated across departments before they are released. An employee who "
         "disagrees with a rating may appeal in writing to the HRD review panel within 14 calendar "
         "days of receiving it. The panel issues a final decision within 21 calendar days."),
        ("5 Link to Compensation",
         "To be eligible for a merit increase an employee needs a year-end rating of 3 or higher and "
         "at least 6 months of service at the review date."),
    ]),
    ("HRD-HB-005", "Staff Onboarding and Probation Handbook", [
        ("1 First Week",
         "New staff attend orientation on their first day and receive a laptop and system accounts. "
         "A buddy from the same team is assigned for the first 30 days to help the new joiner settle "
         "in."),
        ("2 Probation Period",
         "The probation period for new staff is 3 months. It may be extended once, by up to 1 month, "
         "with written reasons. Probation review meetings take place on day 30, day 60 and day 85."),
        ("3 Confirmation and Notice",
         "Staff who pass probation receive written confirmation from HRD. During probation either "
         "party may end the contract with 7 calendar days of notice; after confirmation the notice "
         "period is 30 calendar days."),
        ("4 Benefits During Probation",
         "Health insurance starts on the first day of employment. Annual leave accrues during "
         "probation but cannot be taken until the employee is confirmed. Staff on probation are not "
         "eligible for the training budget."),
        ("5 Required Documents",
         "Within 5 working days of joining, new staff provide a copy of their national ID or passport, "
         "bank account details, a completed tax form and a signed non-disclosure agreement."),
    ]),
    ("HRD-HB-006", "Intern Handbook", [
        ("1 Internship Duration",
         "An internship lasts 6 months. It may be extended once, by 3 months, if the department "
         "requests it and the intern agrees. Interns do not serve a probation period."),
        ("2 Stipend and Time Off",
         "Interns receive a stipend of USD 250 per month, paid on the 25th. Interns are not entitled "
         "to annual leave; they may take 1 day of personal leave per month, and further absence is "
         "unpaid."),
        ("3 Supervision and Evaluation",
         "Each intern is assigned a mentor. The mentor completes a short evaluation every month, and "
         "the intern gives a final presentation in the last week of the internship."),
        ("4 Conversion to Staff",
         "Interns whose final evaluation is Meets expectations or above may be offered a staff "
         "contract. For converted interns the staff probation period is reduced to 1 month."),
        ("5 Equipment and Access",
         "Interns receive a loan laptop and read-only access to the HRIS. All equipment and the "
         "access badge are returned on the last day of the internship."),
    ]),
    ("HRD-IT-007", "HRIS Access and Password Standard", [
        ("1 Authentication",
         "Users sign in to the HRIS through single sign-on using SAML 2.0. Multi-factor authentication "
         "with a TOTP authenticator app is mandatory for every account. SMS one-time codes are not "
         "permitted as a second factor."),
        ("2 Password Requirements",
         "Passwords have a minimum length of 14 characters and are rotated every 180 days. The last 8 "
         "passwords cannot be reused. After 5 failed login attempts the account is locked for 15 "
         "minutes."),
        ("3 Roles and Permissions",
         "The HRIS defines four roles: EMPLOYEE, MANAGER, HR_ADMIN and PAYROLL_ADMIN. Access follows "
         "least privilege. A role change requires a ticket in the HRIS-ACCESS category approved by "
         "the HRD director."),
        ("4 API Tokens",
         "Integrations use service accounts with API tokens. Tokens expire after 90 days, default to "
         "the read:employee scope and are stored in the secrets vault, never in source code. The API "
         "rate limit is 120 requests per minute; requests above the limit receive HTTP 429."),
        ("5 Sessions and Audit",
         "Sessions end after 20 minutes of inactivity. Audit logs are retained for 24 months, and "
         "every export of personal data is logged with the user, time and record count."),
        ("6 Offboarding",
         "HRIS accounts of departing staff are disabled by 18:00 on the last working day and deleted "
         "30 days later."),
    ]),
    ("HRD-POL-008", "Remote Work and Attendance Policy", [
        ("1 Eligibility",
         "Confirmed staff may work remotely for up to 2 days per week with the agreement of their "
         "line manager. Staff on probation and interns are not eligible for remote work."),
        ("2 Working Hours",
         "Standard working hours are 8:00 to 17:00 with a one-hour lunch break. Core hours, when all "
         "staff must be reachable, are 9:30 to 16:00."),
        ("3 Attendance Recording",
         "Staff clock in through the HRIS by 8:15. Three late arrivals in one calendar month result in "
         "a written reminder from the line manager."),
        ("4 Overtime",
         "Overtime must be approved in advance. It is paid at 150% of the hourly rate on weekdays and "
         "200% on Sundays and public holidays, or taken as time off in lieu within 60 days."),
        ("5 Equipment and Security",
         "Remote work is done on the company laptop through the VPN. Public Wi-Fi may be used only "
         "with the VPN connected, and documents containing personal data are not printed at home."),
    ]),
]


def cid(doc, sec_idx):
    return f"{doc}#s{sec_idx}#c01"


Q = [
    # id, type, query, expected chunk ids (any counts as a hit; first = primary), note
    ("Q01", "exact", "What is the maximum number of unused annual leave days that may be carried over to the next year?",
     [cid("HRD-POL-001", 4)], "Wording copied from the chunk."),
    ("Q02", "exact", "After how many failed login attempts is the account locked, and for how long?",
     [cid("HRD-IT-007", 2)], "Wording copied from the chunk."),
    ("Q03", "paraphrased", "I've been ill for three days in a row. Do I have to bring a doctor's note?",
     [cid("HRD-POL-002", 2)], "'doctor's note' vs 'medical certificate'; 'ill' vs 'sick'."),
    ("Q04", "paraphrased", "Can I challenge my appraisal score if I think it is unfair?",
     [cid("HRD-PRO-004", 4)], "'challenge / appraisal score' vs 'appeal / rating'."),
    ("Q05", "short", "overtime rate Sunday",
     [cid("HRD-POL-008", 4)], "Three keywords, no question form."),
    ("Q06", "short", "training bond",
     [cid("HRD-POL-003", 4)], "Two-word query."),
    ("Q07", "long", "I joined six weeks ago and I am still on probation. My sister is getting married abroad next month "
     "and I would like to take a full week off to attend. Am I allowed to use my annual leave already, or do I "
     "have to wait until I have been confirmed?",
     [cid("HRD-HB-005", 4)], "Long with distracting detail (marriage -> special leave chunk is a trap)."),
    ("Q08", "long", "My manager wants me to attend a three-day cloud certification course that costs 1,900 dollars "
     "and starts in about a month. What do I need to submit, who has to sign off given the cost, and would I "
     "owe anything back if I resign next year?",
     [cid("HRD-POL-003", 4), cid("HRD-POL-003", 3), cid("HRD-POL-003", 2)],
     "Multi-part: bond (primary), workflow and budget chunks all count."),
    ("Q09", "technical", "HRIS API token expiry and rate limit for service accounts",
     [cid("HRD-IT-007", 4)], "Technical terms; HTTP 429, scopes."),
    ("Q10", "technical", "Is SMS OTP accepted for MFA, or only TOTP with SAML SSO?",
     [cid("HRD-IT-007", 1)], "Acronym-heavy."),
    ("Q11", "similar-document", "How long does an internship last and can it be extended?",
     [cid("HRD-HB-006", 1)], "Trap: staff probation extension in HRD-HB-005 s2."),
    ("Q12", "similar-document", "Do unused sick days roll over to the next year?",
     [cid("HRD-POL-002", 5)], "Trap: annual leave carry-over in HRD-POL-001 s4."),
    ("Q13", "similar-document", "Can the probation period for new staff be extended, and by how much?",
     [cid("HRD-HB-005", 2)], "Trap: internship extension HRD-HB-006 s1, converted interns s4."),
    ("Q14", "no-answer", "What is the policy on stock options and equity vesting?", [],
     "Topic absent from the corpus."),
    ("Q15", "no-answer", "How many annual leave days do contractors in the Singapore office get?", [],
     "Near-miss: leave is covered, contractors and Singapore are not."),
    ("Q16", "no-answer", "What is the dress code for client meetings?", [],
     "Topic absent from the corpus."),
]


def main():
    chunks = []
    for doc_id, title, sections in DOCS:
        for i, (sec, text) in enumerate(sections, 1):
            chunks.append({"chunk_id": cid(doc_id, i), "doc_id": doc_id, "doc_title": title,
                           "section": sec, "text": text})
    ids = {c["chunk_id"] for c in chunks}
    with open(HERE / "corpus.jsonl", "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    with open(HERE / "queries.jsonl", "w", encoding="utf-8") as f:
        for qid, qtype, text, exp, note in Q:
            assert all(e in ids for e in exp), (qid, exp)
            f.write(json.dumps({"query_id": qid, "type": qtype, "query": text,
                                "expected_chunks": exp, "note": note}, ensure_ascii=False) + "\n")
    print(f"{len(chunks)} chunks, {len(Q)} queries written")


if __name__ == "__main__":
    main()
