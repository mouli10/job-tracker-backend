"""
Demo data generator for testing the Smart Job Application Tracker
This provides sample job-related emails when Gmail API is not available
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Sample companies
COMPANIES = [
    "Google", "Microsoft", "Apple", "Amazon", "Meta", "Netflix", "Twitter", 
    "LinkedIn", "Uber", "Airbnb", "Stripe", "Shopify", "Slack", "Zoom",
    "Salesforce", "Adobe", "Oracle", "IBM", "Intel", "NVIDIA", "AMD",
    "Spotify", "Pinterest", "Snapchat", "TikTok", "Discord", "GitHub",
    "Atlassian", "MongoDB", "Databricks", "Snowflake", "Palantir"
]

# Sample job titles
JOB_TITLES = [
    "Software Engineer", "Frontend Developer", "Backend Developer", 
    "Full Stack Developer", "DevOps Engineer", "Data Scientist",
    "Machine Learning Engineer", "Product Manager", "UX Designer",
    "UI Designer", "QA Engineer", "Site Reliability Engineer",
    "Cloud Engineer", "Security Engineer", "Mobile Developer"
]

# Sample email subjects
EMAIL_SUBJECTS = {
    "applications_sent": [
        "Application Received - {job_title} Position",
        "Thank you for your application - {company}",
        "Application Confirmation - {job_title}",
        "We received your application for {job_title}",
        "Application Status Update - {company}",
        "Your application has been submitted - {job_title}"
    ],
    "rejected": [
        "Application Update - {company}",
        "Thank you for your interest in {company}",
        "Application Status - {job_title} Position",
        "Update regarding your application",
        "Application Decision - {company}",
        "Thank you for applying to {company}"
    ],
    "interview_scheduled": [
        "Interview Invitation - {company}",
        "Schedule your interview - {job_title}",
        "Next Steps - Interview Request",
        "Interview Request - {company}",
        "Let's schedule a call - {job_title}",
        "Interview Invitation - {job_title} Position"
    ],
    "offer_received": [
        "Congratulations! Job Offer - {company}",
        "Offer Letter - {job_title} Position",
        "We're excited to offer you - {company}",
        "Job Offer - {job_title}",
        "Welcome to {company} - Offer Letter",
        "Congratulations! Offer for {job_title}"
    ]
}

# Sample email snippets
EMAIL_SNIPPETS = {
    "applications_sent": [
        "Thank you for your interest in the {job_title} position at {company}. We have received your application and our team will review it carefully.",
        "We confirm that your application for the {job_title} role has been successfully submitted. You will hear from us within the next few days.",
        "Your application for the {job_title} position has been received. Our hiring team will review your qualifications and get back to you soon.",
        "Thank you for applying to {company}. We have received your application for the {job_title} position and will be in touch shortly."
    ],
    "rejected": [
        "Thank you for your interest in the {job_title} position at {company}. After careful consideration, we have decided to move forward with other candidates.",
        "We appreciate your interest in joining {company}. Unfortunately, we have decided not to move forward with your application for the {job_title} position.",
        "Thank you for taking the time to apply for the {job_title} role. We have reviewed your application and regret to inform you that we will not be moving forward.",
        "We appreciate your interest in {company}. After reviewing your application for the {job_title} position, we have decided to pursue other candidates."
    ],
    "interview_scheduled": [
        "We are excited to move forward with your application for the {job_title} position at {company}. Let's schedule an interview to discuss your background and the role.",
        "Congratulations! We would like to invite you for an interview for the {job_title} position. Please let us know your availability for the coming week.",
        "We are pleased to invite you for an interview for the {job_title} role at {company}. This will be a great opportunity to learn more about your experience.",
        "Thank you for your application. We would like to schedule an interview to discuss the {job_title} position and learn more about your qualifications."
    ],
    "offer_received": [
        "Congratulations! We are excited to offer you the {job_title} position at {company}. We believe your skills and experience will be a great addition to our team.",
        "We are pleased to extend you an offer for the {job_title} position. We look forward to having you join the {company} team.",
        "Congratulations! After a thorough interview process, we are excited to offer you the {job_title} role at {company}.",
        "We are delighted to offer you the {job_title} position. We believe you will be an excellent addition to the {company} team."
    ]
}

def generate_demo_emails(count: int = 50) -> List[Dict[str, Any]]:
    """Generate demo email data for testing."""
    emails = []
    
    for i in range(count):
        # Randomly select category with weighted distribution
        category = random.choices(
            ["applications_sent", "rejected", "interview_scheduled", "offer_received"],
            weights=[0.4, 0.3, 0.2, 0.1]
        )[0]
        
        company = random.choice(COMPANIES)
        job_title = random.choice(JOB_TITLES)
        
        # Generate random date within last 6 months
        days_ago = random.randint(0, 180)
        date = datetime.now() - timedelta(days=days_ago)
        
        # Generate email ID
        email_id = f"demo_email_{i:04d}"
        
        # Select random subject and snippet
        subject_template = random.choice(EMAIL_SUBJECTS[category])
        snippet_template = random.choice(EMAIL_SNIPPETS[category])
        
        subject = subject_template.format(company=company, job_title=job_title)
        snippet = snippet_template.format(company=company, job_title=job_title)
        
        # Generate from email
        from_email = f"careers@{company.lower().replace(' ', '')}.com"
        
        # Create Gmail URL (demo)
        gmail_url = f"https://mail.google.com/mail/u/0/#inbox/{email_id}"
        
        email_data = {
            'id': email_id,
            'subject': subject,
            'snippet': snippet,
            'from_email': from_email,
            'date': date.isoformat(),
            'category': category,
            'company': company,
            'gmail_url': gmail_url
        }
        
        emails.append(email_data)
    
    # Sort by date (newest first)
    emails.sort(key=lambda x: x['date'], reverse=True)
    
    return emails

def generate_demo_stats(emails: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate demo statistics from email data."""
    categories = {}
    for email in emails:
        category = email['category']
        categories[category] = categories.get(category, 0) + 1
    
    return {
        'total_applications': len(emails),
        'applications_sent': categories.get('applications_sent', 0),
        'rejected': categories.get('rejected', 0),
        'interview_scheduled': categories.get('interview_scheduled', 0),
        'offer_received': categories.get('offer_received', 0),
        'categories': categories
    }

def generate_demo_email_detail(email_id: str, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate detailed email content for a specific email."""
    email = next((e for e in emails if e['id'] == email_id), None)
    
    if not email:
        return None
    
    # Generate a more detailed body
    company = email['company']
    job_title = email['job_title'] if 'job_title' in email else "Software Engineer"
    category = email['category']
    
    body_templates = {
        "applications_sent": f"""Dear Applicant,

Thank you for your interest in the {job_title} position at {company}. We have successfully received your application and it has been added to our review queue.

Our hiring team will carefully review your qualifications and experience. You can expect to hear from us within the next 5-7 business days regarding the next steps in our hiring process.

In the meantime, if you have any questions about your application, please don't hesitate to reach out to our recruitment team.

Best regards,
The {company} Hiring Team""",
        
        "rejected": f"""Dear Applicant,

Thank you for your interest in the {job_title} position at {company} and for taking the time to apply. We appreciate the effort you put into your application.

After careful consideration of your qualifications and experience, we have decided to move forward with other candidates whose backgrounds more closely align with our current needs for this position.

We were impressed by your application and encourage you to apply for future opportunities at {company} that match your skills and interests. We will keep your resume on file and may reach out if suitable positions become available.

We wish you the best in your job search and future career endeavors.

Best regards,
The {company} Hiring Team""",
        
        "interview_scheduled": f"""Dear Applicant,

We are excited to move forward with your application for the {job_title} position at {company}! We were impressed by your background and would like to schedule an interview to learn more about your experience and discuss the role in detail.

The interview will be conducted via video call and will last approximately 45-60 minutes. During this time, we'll discuss:
- Your background and experience
- The role and responsibilities
- Our team and company culture
- Your questions about the position

Please reply to this email with your availability for the coming week, and we'll schedule a time that works for both parties.

We look forward to meeting you!

Best regards,
The {company} Hiring Team""",
        
        "offer_received": f"""Dear Applicant,

Congratulations! We are thrilled to offer you the {job_title} position at {company}. After a thorough interview process, we are confident that your skills, experience, and values align perfectly with our team and company mission.

Offer Details:
- Position: {job_title}
- Start Date: [To be discussed]
- Compensation: [Details to be provided]
- Benefits: [Full benefits package details]

We believe you will be an excellent addition to our team and look forward to having you join us. Please review the attached offer letter for complete details and let us know if you have any questions.

We're excited to welcome you to {company}!

Best regards,
The {company} Hiring Team"""
    }
    
    body = body_templates.get(category, "Email content not available.")
    
    return {
        'id': email['id'],
        'subject': email['subject'],
        'body': body,
        'from_email': email['from_email'],
        'date': email['date'],
        'category': email['category'],
        'company': email['company'],
        'gmail_url': email['gmail_url']
    }

if __name__ == "__main__":
    # Generate sample data
    emails = generate_demo_emails(20)
    stats = generate_demo_stats(emails)
    
    print("Demo Email Data Generated:")
    print(f"Total emails: {stats['total_applications']}")
    print(f"Applications sent: {stats['applications_sent']}")
    print(f"Rejected: {stats['rejected']}")
    print(f"Interviews: {stats['interview_scheduled']}")
    print(f"Offers: {stats['offer_received']}")
    
    print("\nSample emails:")
    for email in emails[:3]:
        print(f"- {email['subject']} ({email['category']})") 