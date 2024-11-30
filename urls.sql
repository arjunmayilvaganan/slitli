CREATE TABLE urls(
   id SERIAL PRIMARY KEY     NOT NULL,
   longurl           TEXT    NOT NULL,
   alias            TEXT     NOT NULL,
   clicks        INT
);