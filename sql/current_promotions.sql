-- View de "estado atual": a última linha por item_id (preço mais recente).
-- item_id repete por design (modelo de histórico de preços via dedupe_key com preço);
-- esta view separa o estado atual do histórico. Criada pelo app (ensure_view).
CREATE OR REPLACE VIEW `promozone-desafio.promozone.current_promotions` AS
SELECT * EXCEPT(_rn) FROM (
  SELECT *, ROW_NUMBER() OVER (
    PARTITION BY item_id ORDER BY last_seen_at DESC, collected_at DESC, dedupe_key
  ) AS _rn
  FROM `promozone-desafio.promozone.promotions`
)
WHERE _rn = 1;
