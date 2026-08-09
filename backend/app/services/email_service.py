import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config.settings import settings


class EmailService:
    """Serviço de envio de e-mails usando SMTP nativo do Python (smtplib e ssl)."""

    @staticmethod
    def send_verification_email(to_email: str, code: str) -> bool:
        """Envia um e-mail de verificação para o usuário.

        Retorna True se enviado com sucesso, ou se estiver em modo fallback/desenvolvimento.
        """
        # Sempre imprime nos logs para fins de depuração e testes locais
        print("\n" + "=" * 80)
        print(f"CÓDIGO DE VERIFICAÇÃO DE REGISTRO PARA: {to_email}")
        print(f"Código: {code}")
        print("=" * 80 + "\n")

        # Se as credenciais do SMTP não estiverem configuradas, ativa o modo de fallback/mock silencioso
        if not settings.EMAIL_USER or not settings.EMAIL_PASS:
            print("Aviso: EMAIL_USER ou EMAIL_PASS não configurados. Prosseguindo com o fluxo usando apenas log no console.")
            return True

        subject = "Código de Verificação - RIOU"
        html_content = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 5px;">
            <h2 style="color: #801d2a; border-bottom: 2px solid #801d2a; padding-bottom: 10px;">RIOU - Registro Inteligente de Ocorrências Urbanas</h2>
            <p>Olá,</p>
            <p>Obrigado por iniciar o seu cadastro no sistema RIOU.</p>
            <p>Para prosseguir com a criação da sua conta, utilize o código de verificação abaixo na tela de cadastro:</p>
            <div style="background-color: #f8fafc; border: 1px dashed #cbd5e1; padding: 15px; text-align: center; font-size: 28px; font-weight: bold; letter-spacing: 5px; margin: 20px 0; border-radius: 6px; color: #801d2a;">
                {code}
            </div>
            <p style="color: #64748b; font-size: 14px;">Este código expira em 15 minutos.</p>
            <p style="color: #64748b; font-size: 14px; margin-top: 20px; border-top: 1px solid #e2e8f0; padding-top: 10px;">Se você não solicitou este cadastro, por favor ignore este e-mail.</p>
        </div>
        """

        # Criação da mensagem MIME
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.EMAIL_USER
        message["To"] = to_email

        part = MIMEText(html_content, "html", "utf-8")
        message.attach(part)

        try:
            context = ssl.create_default_context()
            
            # Se for a porta de SSL clássica (465)
            if settings.SMTP_PORT == 465:
                with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT, context=context, timeout=10.0) as server:
                    server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
                    server.sendmail(settings.EMAIL_USER, to_email, message.as_string())
            else:
                # Caso contrário, tenta via STARTTLS (porta 587 ou outra)
                with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT, timeout=10.0) as server:
                    server.starttls(context=context)
                    server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
                    server.sendmail(settings.EMAIL_USER, to_email, message.as_string())
            
            return True
        except Exception as e:
            print(f"Aviso: Falha ao enviar e-mail via SMTP ({settings.SMTP_SERVER}:{settings.SMTP_PORT}): {e}")
            print("Como o código foi impresso nos logs acima, prosseguindo com o fluxo (fallback de desenvolvimento/sandbox).")
            return True
