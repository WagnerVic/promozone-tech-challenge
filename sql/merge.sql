-- MERGE executado pelo app a cada coleta (BigQueryService._merge).
-- A staging é por execução (staging_<execution_id>), carregada via load job.
-- WHEN NOT MATCHED -> nova promoção (insere). WHEN MATCHED -> já existe (só atualiza last_seen_at).
-- O QUALIFY deduplica a staging por dedupe_key (rede de segurança: o MERGE exige no máximo
-- 1 linha-fonte por linha-alvo; chave repetida abortaria ou inseriria duplicado).
MERGE `promozone-desafio.promozone.promotions` T
USING (
  SELECT * FROM `promozone-desafio.promozone.staging_<execution_id>`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY dedupe_key ORDER BY collected_at DESC) = 1
) S
ON T.dedupe_key = S.dedupe_key
WHEN NOT MATCHED THEN
  INSERT (marketplace, item_id, url, title, price, original_price, discount_percent,
          seller, image_url, source, currency, category, category_name, promotion_type,
          dedupe_key, execution_id, collected_at, inserted_at, last_seen_at)
  VALUES (S.marketplace, S.item_id, S.url, S.title, S.price, S.original_price, S.discount_percent,
          S.seller, S.image_url, S.source, S.currency, S.category, S.category_name, S.promotion_type,
          S.dedupe_key, S.execution_id, S.collected_at, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP())
WHEN MATCHED THEN
  -- category congela (first-write, estável por item); promotion_type atualiza
  -- (last-write, "atual = visto por último", igual à view current_promotions).
  UPDATE SET last_seen_at = CURRENT_TIMESTAMP(), promotion_type = S.promotion_type;
