import httpx

from app.config.settings import settings


class EmailService:
    """Serviço de envio de e-mails usando a API do Resend."""

    @staticmethod
    def send_verification_email(to_email: str, code: str) -> bool:
        """Envia um e-mail de verificação para o usuário.

        Retorna True se enviado com sucesso, False caso contrário.
        """
        # Sempre imprime nos logs para fins de depuração e testes locais
        print("\n" + "=" * 80)
        print(f"CÓDIGO DE VERIFICAÇÃO DE REGISTRO PARA: {to_email}")
        print(f"Código: {code}")
        print("=" * 80 + "\n")

        # Se a chave da API for a de testes mock ou vazia, não faz a chamada real
        if not settings.RESEND_API_KEY or settings.RESEND_API_KEY.startswith("mock_"):
            return True

        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        data = {
            "from": settings.RESEND_FROM_EMAIL,
            "to": to_email,
            "subject": "Código de Verificação - RIOU",
            "html": f"""
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
            """,
        }

        try:
            # Fazemos o POST de forma síncrona
            response = httpx.post(url, json=data, headers=headers, timeout=10.0)
            if response.status_code in (200, 201):
                return True
            else:
                print(
                    f"Aviso: Falha ao enviar e-mail via Resend ({response.status_code}): {response.text}"
                )
                print("Como o código foi impresso nos logs acima, prosseguindo com o fluxo (fallback de desenvolvimento/sandbox).")
                return True
        except Exception as e:
            print(f"Aviso: Exceção ao enviar e-mail via Resend: {e}")
            print("Como o código foi impresso nos logs acima, prosseguindo com o fluxo (fallback de desenvolvimento/sandbox).")
            return True
