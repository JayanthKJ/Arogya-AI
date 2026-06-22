import logging
import resend
from config.settings import get_settings

logger = logging.getLogger(__name__)

def send_password_reset_email(email: str, reset_link: str):
    settings = get_settings()
    
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY is not set. Email will not be sent.")
        return

    resend.api_key = settings.RESEND_API_KEY
    
    html_content = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
        <div style="text-align: center; padding: 20px;">
            <h1 style="color: #115e59; margin-bottom: 5px;">🌿 Arogya AI</h1>
            <p style="color: #0d9488; font-size: 14px; margin-top: 0; letter-spacing: 1px;">HEALTH COMPANION</p>
        </div>
        
        <div style="padding: 20px; background-color: #f9fafb; border-radius: 12px; border: 1px solid #f3f4f6;">
            <h2 style="color: #1f2937; font-size: 20px;">Password Reset Request</h2>
            <p style="font-size: 16px; line-height: 1.5;">Hello,</p>
            <p style="font-size: 16px; line-height: 1.5;">We received a request to reset your password for your Arogya AI account. Click the button below to set a new password:</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background-color: #0f766e; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Reset Password</a>
            </div>
            
            <p style="font-size: 14px; line-height: 1.5; color: #4b5563;">Or copy and paste this link into your browser:</p>
            <p style="font-size: 14px; color: #0d9488; word-break: break-all;">{reset_link}</p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 14px; color: #6b7280; margin-bottom: 5px;"><strong>Note:</strong> This link will expire in 10 minutes.</p>
                <p style="font-size: 14px; color: #6b7280; margin-top: 0;">If you did not request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
            </div>
        </div>
    </div>
    """

    try:
        response = resend.Emails.send({
            "from": settings.EMAIL_FROM,
            "to": email,
            "subject": "Reset Your Password - Arogya AI",
            "html": html_content
        })
        logger.info(f"Password reset email sent successfully to {email}. Resend ID: {response.get('id')}")
    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}: {str(e)}")
