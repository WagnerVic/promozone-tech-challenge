"""Persistência no BigQuery via staging por execução + MERGE (dedupe idempotente)."""
from __future__ import annotations

from google.api_core.exceptions import Conflict
from google.cloud import bigquery

from app.core.config import settings
from app.core.logging import get_logger
from app.models.product import ProductSchema

logger = get_logger(__name__)

# Colunas da staging = campos serializados do ProductSchema (model_dump(mode="json")).
_STAGING_SCHEMA = [
    bigquery.SchemaField("marketplace", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("item_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("url", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("price", "NUMERIC", mode="REQUIRED"),
    bigquery.SchemaField("original_price", "NUMERIC"),
    bigquery.SchemaField("discount_percent", "FLOAT64"),
    bigquery.SchemaField("seller", "STRING"),
    bigquery.SchemaField("image_url", "STRING"),
    bigquery.SchemaField("source", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("currency", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("category", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("category_name", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("promotion_type", "STRING"),
    bigquery.SchemaField("dedupe_key", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("execution_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("collected_at", "TIMESTAMP", mode="REQUIRED"),
]
# Tabela final = staging + timestamps definidos server-side no MERGE.
_TABLE_SCHEMA = _STAGING_SCHEMA + [
    bigquery.SchemaField("inserted_at", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("last_seen_at", "TIMESTAMP", mode="REQUIRED"),
]
_COLS = [f.name for f in _STAGING_SCHEMA]


class BigQueryService:
    def __init__(self) -> None:
        if not settings.GOOGLE_CLOUD_PROJECT:
            raise RuntimeError(
                "GOOGLE_CLOUD_PROJECT não definido — configure no .env antes de persistir."
            )
        self.client = bigquery.Client(
            project=settings.GOOGLE_CLOUD_PROJECT, location=settings.BQ_LOCATION
        )
        ds = settings.GCP_DATASET_ID
        self.table_id = f"{self.client.project}.{ds}.{settings.BQ_TABLE}"
        self.view_id = f"{self.client.project}.{ds}.current_promotions"
        self._dataset = ds

    def ensure_table(self) -> None:
        table = bigquery.Table(self.table_id, schema=_TABLE_SCHEMA)
        table.time_partitioning = bigquery.TimePartitioning(field="collected_at")
        table.clustering_fields = ["dedupe_key"]
        try:
            self.client.create_table(table)
            self.ensure_view()  # view criada só quando a tabela nasce (evita DDL a cada run)
        except Conflict:
            pass  # tabela já existe

    def ensure_view(self) -> None:
        # "Estado atual": última linha por item_id (separa atual do histórico de preços).
        # "Atual = visto por último" → last_seen_at é a CHAVE de ordenação (não desempate):
        # com preço oscilante (100→90→100), a linha de 100 é revista (MATCHED) e tem o
        # last_seen_at mais recente; ordenar por collected_at elegeria a linha morta de 90.
        sql = f"""
            CREATE OR REPLACE VIEW `{self.view_id}` AS
            SELECT * EXCEPT(_rn) FROM (
              SELECT *, ROW_NUMBER() OVER (
                PARTITION BY item_id ORDER BY last_seen_at DESC, collected_at DESC, dedupe_key
              ) AS _rn
              FROM `{self.table_id}`
            )
            WHERE _rn = 1
        """
        self.client.query(sql).result()

    def upsert(self, products: list[ProductSchema], execution_id: str) -> dict:
        if not products:
            return {"inserted": 0, "duplicates": 0}

        self.ensure_table()
        staging_id = f"{self.client.project}.{self._dataset}.staging_{execution_id}"
        rows = [p.model_dump(mode="json") for p in products]

        try:
            self.client.load_table_from_json(
                rows,
                staging_id,
                job_config=bigquery.LoadJobConfig(
                    schema=_STAGING_SCHEMA, write_disposition="WRITE_TRUNCATE"
                ),
            ).result()

            # MERGE devolve só o total afetado; contamos os já existentes ANTES dele.
            duplicates = self._count_existing(staging_id)
            self._merge(staging_id)
            inserted = len(products) - duplicates

            logger.info(
                "bigquery upsert",
                extra={"execution_id": execution_id, "inserted": inserted,
                       "duplicates": duplicates},
            )
            return {"inserted": inserted, "duplicates": duplicates}
        finally:
            self.client.delete_table(staging_id, not_found_ok=True)

    def _count_existing(self, staging_id: str) -> int:
        sql = f"""
            SELECT COUNT(*) AS n
            FROM `{staging_id}` s
            WHERE EXISTS (SELECT 1 FROM `{self.table_id}` t WHERE t.dedupe_key = s.dedupe_key)
        """
        return next(iter(self.client.query(sql).result())).n

    def _merge(self, staging_id: str) -> None:
        # Semântica de atualização na linha (item, preço) já existente:
        # - category é estável por item → first-write (congela na 1ª observação);
        # - promotion_type é volátil → last-write (atualiza), alinhado a "atual = visto
        #   por último" (mesma semântica da view current_promotions).
        cols = ", ".join(_COLS)
        s_cols = ", ".join(f"S.{c}" for c in _COLS)
        sql = f"""
            MERGE `{self.table_id}` T
            USING (
              SELECT * FROM `{staging_id}`
              QUALIFY ROW_NUMBER() OVER (PARTITION BY dedupe_key ORDER BY collected_at DESC) = 1
            ) S
            ON T.dedupe_key = S.dedupe_key
            WHEN NOT MATCHED THEN
              INSERT ({cols}, inserted_at, last_seen_at)
              VALUES ({s_cols}, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP())
            WHEN MATCHED THEN
              UPDATE SET last_seen_at = CURRENT_TIMESTAMP(), promotion_type = S.promotion_type
        """
        self.client.query(sql).result()
