CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name VARCHAR(80) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    titre VARCHAR(120) NOT NULL,
    description TEXT,
    tarif_jour NUMERIC(10, 2) NOT NULL CHECK (tarif_jour > 0),
    disponible BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE reservations (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    borrower_id INTEGER NOT NULL REFERENCES users(id),
    date_debut DATE NOT NULL,
    date_fin DATE NOT NULL,
    statut TEXT NOT NULL DEFAULT 'active'
        CHECK (statut IN ('active', 'annulee', 'terminee')),
    CONSTRAINT reservations_dates_check CHECK (date_fin > date_debut)
);
