-- Tabela final de promoções. O app cria automaticamente (ensure_table);
-- este arquivo documenta o schema. Troque o projeto/dataset se necessário.
CREATE TABLE IF NOT EXISTS `promozone-desafio.promozone.promotions` (
  marketplace      STRING    NOT NULL,
  item_id          STRING    NOT NULL,   -- catálogo 'MLB123' ou anúncio 'MLB-123'
  url              STRING    NOT NULL,
  title            STRING    NOT NULL,
  price            NUMERIC   NOT NULL,   -- dinheiro exato (sem float)
  original_price   NUMERIC,
  discount_percent FLOAT64,
  seller           STRING,
  image_url        STRING,
  source           STRING    NOT NULL,   -- vitrine que gerou o item
  currency         STRING    NOT NULL,
  category         STRING    NOT NULL,   -- id da categoria de ofertas (MLB....)
  category_name    STRING    NOT NULL,   -- nome legível da categoria
  promotion_type   STRING,               -- badge do card (oferta relâmpago/do dia/...); nullable
  dedupe_key       STRING    NOT NULL,   -- marketplace + item_id + price
  execution_id     STRING    NOT NULL,
  collected_at     TIMESTAMP NOT NULL,
  inserted_at      TIMESTAMP NOT NULL,   -- 1ª vez vista (server-side no MERGE)
  last_seen_at     TIMESTAMP NOT NULL    -- última vez vista (atualizada no MERGE)
)
PARTITION BY DATE(collected_at)          -- consultas por data varrem menos
CLUSTER BY dedupe_key;                   -- acelera o JOIN do MERGE/dedupe
