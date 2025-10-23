import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from app.config import settings
from app.log import get_logger

log = get_logger(__name__)


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email to the specified recipients.
        
        Parameters:
            to_emails (List[str]): List of recipient email addresses
            subject (str): Email subject
            html_content (str): HTML content of the email
            text_content (Optional[str]): Plain text content of the email
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            
            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            if not self.smtp_username or not self.smtp_password:
                log.warning("SMTP credentials not configured. Email not sent.")
                log.info(f"Would send email to {to_emails} with subject: {subject}")
                log.debug(f"Email content: {html_content}")
                return True 
            
            # Send email
            if self.smtp_port == 465:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
            
            log.info(f"Email sent successfully to {to_emails}")
            return True
            
        except Exception as e:
            log.error(f"Failed to send email to {to_emails}: {str(e)}")
            return False
    
    def send_password_reset_email(self, email: str, reset_token: str, user_nickname: str) -> bool:
        """
        Send a password reset email to the user.
        
        Parameters:
            email (str): User's email address
            reset_token (str): Password reset token
            user_nickname (str): User's nickname
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        subject = "Réinitialisation du mot de passe 321 Vegan"
        
        frontend_url = settings.FRONTEND_URL
        reset_url = f"{frontend_url}/reset-password?token={reset_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Réinitialisation du mot de passe</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                <h1 style="color: #2c5530; text-align: center; margin-bottom: 30px;">
                    🌱 321Vegan
                </h1>
                
                <h2 style="color: #333; margin-bottom: 20px;">
                    Bonjour {user_nickname},
                </h2>
                
                <p style="margin-bottom: 20px;">
                    Nous avons reçu une demande de réinitialisation de votre mot de passe pour votre compte sur 321Vegan.
                    Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet e-mail.
                </p>
                
                <p style="margin-bottom: 30px;">
                    Pour réinitialiser votre mot de passe, cliquez sur le bouton ci-dessous :
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #2c5530; color: white; padding: 15px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;
                              font-weight: bold;">
                        Réinitialiser mon mot de passe
                    </a>
                </div>
                
                <p style="margin-bottom: 20px; font-size: 14px; color: #666;">
                    Si le bouton ci-dessus ne fonctionne pas, copiez et collez le lien suivant dans votre navigateur :
                </p>
                
                <p style="margin-bottom: 30px; word-break: break-all; font-size: 14px; color: #666;">
                    {reset_url}
                </p>
                
                <p style="margin-bottom: 10px; font-size: 14px; color: #666;">
                    Ce lien de réinitialisation expirera dans 24 heures pour des raisons de sécurité.
                </p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                
                <p style="font-size: 12px; color: #999; text-align: center;">
                    Cet e-mail a été envoyé par 321 Vegan. Si vous avez des questions, n'hésitez pas à nous contacter !
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Bonjour {user_nickname},

        Nous avons reçu une demande de réinitialisation de votre mot de passe pour votre compte sur 321Vegan.
        Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet e-mail.

        Pour réinitialiser votre mot de passe, veuillez visiter le lien suivant :
        {reset_url}

        Ce lien de réinitialisation expirera dans 24 heures pour des raisons de sécurité.

        A bientôt !
        L'équipe de 321Vegan
        """
        
        return self.send_email([email], subject, html_content, text_content)


# Create a singleton instance
email_service = EmailService()