from src.ingestion.embedding.base_embed import TemplateEmbedder
from src.ingestion.embedding.embedder import SentenceTransformerEmbedder
from src.utils.config import settings


def get_embedder() -> TemplateEmbedder:
    embed_settings = settings.embedding
    if embed_settings.provider == "sentence_transformers":
        return SentenceTransformerEmbedder(
            expected_dim=embed_settings.dimensions,
            model_name=embed_settings.model_name,
            batch_size=embed_settings.batch_size,
            device=embed_settings.device,
        )
    else:
        raise RuntimeError("Invalid provider name")
