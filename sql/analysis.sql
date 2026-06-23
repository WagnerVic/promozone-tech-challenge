-- Relatório de métricas das promoções coletadas (exemplos para o README).
-- Trocam projeto/dataset se necessário.

-- 1) Por categoria: volume e desconto médio.
SELECT
  category_name,
  COUNT(*)                          AS promocoes,
  COUNT(DISTINCT item_id)           AS itens_distintos,
  ROUND(AVG(discount_percent), 1)   AS desconto_medio_pct,
  ROUND(MAX(discount_percent), 1)   AS maior_desconto_pct
FROM `promozone-desafio.promozone.promotions`
GROUP BY category_name
ORDER BY promocoes DESC;

-- 2) Por tipo de promoção (relâmpago / do dia / imperdível / comum=NULL).
SELECT
  IFNULL(promotion_type, 'COMUM')   AS tipo,
  COUNT(*)                          AS promocoes,
  ROUND(AVG(discount_percent), 1)   AS desconto_medio_pct
FROM `promozone-desafio.promozone.promotions`
GROUP BY tipo
ORDER BY promocoes DESC;

-- 3) Cruzamento categoria x tipo de promoção.
SELECT
  category_name,
  IFNULL(promotion_type, 'COMUM')   AS tipo,
  COUNT(*)                          AS promocoes
FROM `promozone-desafio.promozone.promotions`
GROUP BY category_name, tipo
ORDER BY category_name, promocoes DESC;
