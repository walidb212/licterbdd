-- Table decathlon_products pour corrélation avis/produits
CREATE TABLE IF NOT EXISTS decathlon_products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT NOT NULL,
  titre TEXT NOT NULL,
  slug TEXT NOT NULL,
  image_url TEXT,
  marque_detectee TEXT,
  categorie TEXT
);

CREATE INDEX IF NOT EXISTS idx_products_slug ON decathlon_products(slug);
CREATE INDEX IF NOT EXISTS idx_products_categorie ON decathlon_products(categorie);
CREATE INDEX IF NOT EXISTS idx_products_marque ON decathlon_products(marque_detectee);
