

import os
import resend


resend.api_key = os.getenv("RESEND_API_KEY")

def send_email(to_email, subject, body):
    try:
        params = {
            "from": "Your App <onboarding@resend.dev>",  
            "to": [to_email],
            "subject": subject,
            "html": f"<p>{body}</p>",
        }

        response = resend.Emails.send(params)
        return response  
    except Exception as e:
        return {"error": str(e)}
