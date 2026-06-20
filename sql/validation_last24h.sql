-- Query de validação: o que foi coletado nas últimas 24h.
SELECT
  COUNT(*)                        AS linhas,
  COUNT(DISTINCT item_id)         AS itens_distintos,
  COUNT(DISTINCT execution_id)    AS execucoes,
  COUNTIF(discount_percent > 0)   AS com_desconto,
  ROUND(AVG(discount_percent), 1) AS desconto_medio_pct,
  MIN(collected_at)               AS primeira_coleta,
  MAX(collected_at)               AS ultima_coleta
FROM `promozone-desafio.promozone.promotions`
WHERE collected_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR);
