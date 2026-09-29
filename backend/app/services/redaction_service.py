import re

def redact_secrets(text: str) -> str:
    if not text:
        return ""
    
    redacted = text
    
    # 1. API Keys and Tokens (e.g. sk-live-..., ghp_..., Bearer ..., secret=...)
    redacted = re.sub(r'(sk-[a-zA-Z0-9_\-]{20,})', '[REDACTED_API_KEY]', redacted)
    redacted = re.sub(r'(ghp_[a-zA-Z0-9]{36})', '[REDACTED_GITHUB_TOKEN]', redacted)
    redacted = re.sub(r'Bearer\s+([a-zA-Z0-9\._\-]+)', 'Bearer [REDACTED_JWT_TOKEN]', redacted, flags=re.IGNORECASE)
    
    # 2. Key-Value Passwords & Secret Tokens
    redacted = re.sub(r'(?i)(password|passwd|secret|api_key|token|access_key)=([^\s&,;]+)', r'\1=[REDACTED]', redacted)
    
    # 3. Emails
    redacted = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[REDACTED_EMAIL]', redacted)
    
    # 4. IPv4 Addresses (preserve common local/standard non-sensitive subnet markers if desired, or redact all)
    redacted = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[REDACTED_IP]', redacted)
    
    return redacted
