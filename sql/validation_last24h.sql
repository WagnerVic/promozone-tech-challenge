-- Query de validação: o que foi coletado nas últimas 24h (janela rolante).
-- Timestamps exibidos em horário de Brasília (os dados são gravados em UTC).
-- COUNTIF(discount_percent > 0) é um check de integridade: como só persistimos
-- promoção real, com_desconto DEVE ser igual a linhas (se vier menor, o filtro vazou).
SELECT
  DATETIME(CURRENT_TIMESTAMP(), 'America/Sao_Paulo')  AS momento_consulta,
  COUNT(*)                                            AS linhas,
  COUNT(DISTINCT item_id)                             AS itens_distintos,
  COUNT(DISTINCT execution_id)                        AS execucoes,
  COUNT(DISTINCT source)                              AS fontes,
  COUNTIF(discount_percent > 0)                       AS com_desconto,
  ROUND(AVG(discount_percent), 1)                     AS desconto_medio_pct,
  DATETIME(MIN(collected_at), 'America/Sao_Paulo')    AS primeira_coleta,
  DATETIME(MAX(collected_at), 'America/Sao_Paulo')    AS ultima_coleta
FROM `promozone-desafio.promozone.promotions`
WHERE collected_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR);
