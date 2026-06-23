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

-- 4) Top 10 maiores descontos no estado atual (view current_promotions = última linha por item).
SELECT
  title,
  category_name,
  original_price                    AS de,
  price                             AS por,
  discount_percent                  AS desconto_pct,
  IFNULL(promotion_type, 'COMUM')   AS tipo
FROM `promozone-desafio.promozone.current_promotions`
WHERE discount_percent IS NOT NULL
ORDER BY discount_percent DESC
LIMIT 10;

-- 5) Mudanças de preço (o diferencial: o dedupe_key inclui preço → histórico).
--    Itens vistos em mais de um preço; mostra mín/máx, preço atual e a variação.
WITH historico AS (
  SELECT
    item_id,
    COUNT(DISTINCT price) AS precos_distintos,
    MIN(price)            AS menor_preco,
    MAX(price)            AS maior_preco
  FROM `promozone-desafio.promozone.promotions`
  GROUP BY item_id
  HAVING COUNT(DISTINCT price) > 1
)
SELECT
  cur.title,
  cur.category_name,
  h.menor_preco,
  h.maior_preco,
  cur.price                                                   AS preco_atual,
  ROUND((h.maior_preco - h.menor_preco) / h.maior_preco * 100, 1) AS variacao_pct
FROM historico h
JOIN `promozone-desafio.promozone.current_promotions` cur USING (item_id)
ORDER BY variacao_pct DESC
LIMIT 10;

-- 6) Top 10 lojas por número de promoções no estado atual.
SELECT
  seller,
  COUNT(*)                          AS promocoes,
  ROUND(AVG(discount_percent), 1)   AS desconto_medio_pct
FROM `promozone-desafio.promozone.current_promotions`
WHERE seller IS NOT NULL
GROUP BY seller
ORDER BY promocoes DESC
LIMIT 10;
