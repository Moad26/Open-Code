from src.ingestion.embedding.base_embed import TemplateEmbedder
from src.ingestion.embedding.embedder import SentenceTransformerEmbedder
from src.utils.config import settings

_embedder_instance: TemplateEmbedder | None = None


def get_embedder() -> TemplateEmbedder:
    global _embedder_instance

    if _embedder_instance is not None:
        return _embedder_instance

    embed_settings = settings.embedding

    if embed_settings.provider == "sentence_transformers":
        _embedder_instance = SentenceTransformerEmbedder(
            expected_dim=embed_settings.dimensions,
            model_name=embed_settings.model_name,
            batch_size=embed_settings.batch_size,
            device=embed_settings.device,
        )
        return _embedder_instance

    raise ValueError(f"Unsupported embedder provider: {embed_settings.provider}")


"""def get_embedder():
    global _embedder_instance
    embed_settings = settings.embedding
    if embed_settings.provider == "sentence_transformers":
        if _embedder_instance is None:
            _embedder_instance = SentenceTransformerEmbedder(
            expected_dim=embed_settings.dimensions,
            model_name=embed_settings.model_name,
            batch_size=embed_settings.batch_size,
            device=embed_settings.device,
        )
    return _embedder_instance"""

""" def get_embedder() -> TemplateEmbedder:
    embed_settings = settings.embedding
    if embed_settings.provider == "sentence_transformers":

        return SentenceTransformerEmbedder(
            expected_dim=embed_settings.dimensions,
            model_name=embed_settings.model_name,
            batch_size=embed_settings.batch_size,
            device=embed_settings.device,
        )
    else:
        raise RuntimeError("Invalid provider name") """
