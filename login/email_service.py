

import os
import resend


resend.api_key = os.getenv("RESEND_API_KEY")

def send_email(to_email, subject, body):
    print("send mail it being called")
    try:
        params = {
            "from": "noreply@sdo-webinar-evaluation-system.xyz",  
            "to": [to_email],
            "subject": subject,
            "html": f"<p>{body}</p>",
        }

        response = resend.Emails.send(params)
        print("✅ Email sent successfully")
        print("Response:", response)
        return response  
    except Exception as e:
        print(os.getenv("RESEND_API_KEY"))
        print("❌ Failed to send email:", e)
        import traceback
        print("❌ Failed to send email:", e)
        traceback.print_exc()
        return {"error": str(e)}
    
    
