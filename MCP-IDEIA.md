# Ideia de Servidor MCP — EQ20

**Domínio:** Registro Inteligente de Ocorrências Urbanas (Resend/S3)  
**Data:** 2026-07-01

## O que é

Um **servidor MCP (Model Context Protocol)** expõe as operações do seu sistema como *tools* e *resources* que qualquer assistente de IA (Claude Desktop, Cursor, etc.) pode chamar com segurança. Na prática, é uma camada fina sobre a **API que vocês já têm** — cada tool chama um endpoint/service existente. Assim o projeto deixa de ser só uma tela e passa a ser operável por um agente de IA.

## Servidor proposto: `riou-mcp`

### Tools sugeridas

- `registrar_ocorrencia(tipo, local, foto)` — abre ocorrência
- `consultar_status(ocorrenciaId)` — situação
- `ocorrencias_por_regiao(bairro)` — agrega por região
- `notificar_cidadao(userId, msg)` — atualiza o cidadão

### Resources (somente leitura)

- mapa/lista de ocorrências como resource

### Exemplos de uso com um LLM

- "Registre um buraco na Rua X com esta foto."
- "Quais bairros têm mais ocorrências de iluminação?"

## Esqueleto para começar (Python / FastMCP)

```python
# pip install mcp httpx
from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("riou-mcp")
API = "http://localhost:8000"   # sua API local (ajuste a porta)

@mcp.tool()
def registrar_ocorrencia(tipo, local, foto):
    """abre ocorrência"""
    r = httpx.get(f"{API}/seu/endpoint")   # reaproveite sua API existente
    return r.json()

if __name__ == "__main__":
    mcp.run()   # transporte stdio; registre no Claude Desktop / Cursor
```

## Boas práticas

- **Segurança:** cada tool que altera dados deve exigir autenticação e registrar no **log de auditoria** (o mesmo do requisito da disciplina).
- **Escopo mínimo:** exponha só o necessário; separe tools de leitura das de escrita.
- **Reaproveite:** as tools devem chamar seus *services*/*controllers* existentes, não reimplementar regra de negócio.

## Referências
- Documentação MCP: https://modelcontextprotocol.io
- SDKs: Python (`mcp`), TypeScript (`@modelcontextprotocol/sdk`), Java (Spring AI MCP Server).

*Sugestão gerada em 2026-07-01 para orientar a integração de LLMs ao projeto.*