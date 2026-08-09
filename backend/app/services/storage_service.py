"""Serviço de armazenamento de arquivos compatível com S3 (MinIO)."""

import boto3
from botocore.exceptions import ClientError
from app.config.settings import settings

def get_s3_client():
    """Retorna uma instância configurada do cliente S3 (boto3)."""
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
    )

def init_s3():
    """Garante que o bucket configurado existe no S3/MinIO."""
    s3_client = get_s3_client()
    try:
        s3_client.head_bucket(Bucket=settings.S3_BUCKET)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code in ("404", "NoSuchBucket"):
            try:
                # Criar o bucket se ele não existir
                s3_client.create_bucket(Bucket=settings.S3_BUCKET)
                print(f"Bucket '{settings.S3_BUCKET}' criado com sucesso.")
            except Exception as create_err:
                print(f"Erro ao criar bucket '{settings.S3_BUCKET}': {create_err}")
                raise create_err
        else:
            print(f"Erro ao acessar bucket: {e}")
            raise e

def upload_file_to_s3(file_content: bytes, file_name: str, content_type: str) -> str:
    """Realiza o upload do arquivo para o S3/MinIO e retorna sua URL pública."""
    s3_client = get_s3_client()
    
    # Tenta usar ACL public-read. Se o servidor de S3 tiver ACLs desativadas, faz fallback sem ACL.
    try:
        s3_client.put_object(
            Bucket=settings.S3_BUCKET,
            Key=file_name,
            Body=file_content,
            ContentType=content_type,
            ACL="public-read"
        )
    except ClientError:
        s3_client.put_object(
            Bucket=settings.S3_BUCKET,
            Key=file_name,
            Body=file_content,
            ContentType=content_type
        )
        
    # Constrói e retorna a URL pública de acesso direto ao arquivo
    return f"{settings.S3_PUBLIC_ENDPOINT.rstrip('/')}/{settings.S3_BUCKET}/{file_name}"
