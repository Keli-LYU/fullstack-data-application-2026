-- Rule mapping before DDL:
-- Review score: SMALLINT + NOT NULL + named CHECK (1..5).
-- Optional comment: nullable TEXT; author is the reservation's borrower.
-- Completed reservation: constant checked status + composite foreign key.
-- Exactly one reservation per review: NOT NULL foreign key.
-- At most one review per reservation: named UNIQUE (reservation_id).
-- Tags: unique lowercase label; many-to-many item_tags with composite PK.
-- Active booking overlap: partial GiST exclusion constraint, not an app check.
-- Authentication/authorization of the connected caller belongs to the app.

BEGIN;

CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Spell out the existing default deletion policy without changing its behavior.
ALTER TABLE reservations
    DROP CONSTRAINT reservations_borrower_id_fkey,
    ADD CONSTRAINT reservations_borrower_id_fkey
        FOREIGN KEY (borrower_id) REFERENCES users(id) ON DELETE NO ACTION;

ALTER TABLE reservations
    ADD CONSTRAINT reservations_id_statut_key UNIQUE (id, statut),
    ADD CONSTRAINT reservations_active_no_overlap
        EXCLUDE USING gist (
            item_id WITH =,
            daterange(date_debut, date_fin, '[)') WITH &&
        ) WHERE (statut = 'active');

CREATE TABLE avis (
    id SERIAL,
    reservation_id INTEGER NOT NULL,
    reservation_statut TEXT NOT NULL DEFAULT 'terminee',
    note SMALLINT NOT NULL,
    commentaire TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT avis_pkey PRIMARY KEY (id),
    CONSTRAINT avis_reservation_key UNIQUE (reservation_id),
    CONSTRAINT avis_note_check CHECK (note BETWEEN 1 AND 5),
    CONSTRAINT avis_reservation_statut_check
        CHECK (reservation_statut = 'terminee'),
    CONSTRAINT avis_reservation_fkey
        FOREIGN KEY (reservation_id, reservation_statut)
        REFERENCES reservations(id, statut) ON DELETE RESTRICT
);

CREATE TABLE tags (
    id SERIAL,
    libelle VARCHAR(80) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT tags_pkey PRIMARY KEY (id),
    CONSTRAINT tags_libelle_key UNIQUE (libelle),
    CONSTRAINT tags_libelle_lower_check CHECK (libelle = lower(libelle))
);

CREATE TABLE item_tags (
    item_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    CONSTRAINT item_tags_pkey PRIMARY KEY (item_id, tag_id),
    CONSTRAINT item_tags_item_fkey
        FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    CONSTRAINT item_tags_tag_fkey
        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Full FK indexes: the partial exclusion index does not cover inactive bookings.
CREATE INDEX idx_items_owner_id ON items (owner_id);
CREATE INDEX idx_reservations_item_id ON reservations (item_id);
CREATE INDEX idx_reservations_borrower_id ON reservations (borrower_id);
CREATE INDEX idx_item_tags_tag_id ON item_tags (tag_id);
-- avis_reservation_key indexes the unique reservation_id: at most one row
-- can match a composite FK lookup, so another index there is unnecessary.
-- item_tags_pkey already indexes its leading item_id column.

COMMIT;
