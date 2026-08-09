"""Constantes compartilhadas da aplicação."""

CATEGORIES_AND_TYPES: dict[str, list[str]] = {
    "infraestrutura": ["buracos em ruas", "problemas de infraestrutura"],
    "iluminação": ["iluminação pública quebrada"],
    "limpeza urbana": ["lixo acumulado", "descarte irregular de lixo"],
    "trânsito": ["sinalização danificada"],
    "saneamento": ["vazamentos"],
    "segurança pública": ["assaltos", "furtos", "vandalismo", "riscos à segurança pública"],
    "meio ambiente": ["poluição", "problemas ambientais"],
    "saúde urbana": ["focos de dengue"],
    "proteção animal": ["animais abandonados"],
    "emergências urbanas": ["situações de risco urbano"],
}
