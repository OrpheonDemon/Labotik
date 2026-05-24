from .ollama_client import OllamaClient
from .prompts import SYSTEM_PROMPT, OBSERVATION_PROMPT_TEMPLATE


class ObservationGenerator:
    def __init__(self, ollama_client: OllamaClient):
        self.client = ollama_client

    def build_prompt(self, results: list[dict]) -> str:
        laboratory_data = "\n".join([
            f"- {item.get('nombre')}: {item.get('resultado','N/A')} {item.get('unidad','')} (ref: {item.get('valor_referencia','N/A')})"
            for item in results
        ])
        return OBSERVATION_PROMPT_TEMPLATE.format(
            system_prompt=SYSTEM_PROMPT,
            laboratory_data=laboratory_data
        )

    async def generate(self, results: list[dict]) -> dict[str, str]:
        prompt = self.build_prompt(results)
        raw_response = await self.client.generate(prompt)
        return self._parse_response(raw_response)

    def _parse_response(self, text: str) -> dict[str, str]:
        observation_text = ""
        conclusion_text = ""
        lines = text.splitlines()
        section = None
        for line in lines:
            lower = line.strip().lower()
            if lower.startswith('observaciones clínicas:'):
                section = 'observaciones'
                continue
            if lower.startswith('conclusión preliminar:') or lower.startswith('conclusion preliminar:'):
                section = 'conclusion'
                continue
            if section == 'observaciones':
                observation_text += line.strip(' -*') + '\n'
            elif section == 'conclusion':
                conclusion_text += line.strip() + ' '
        return {
            'observaciones_clinicas': observation_text.strip(),
            'conclusion_preliminar': conclusion_text.strip()
        }
