DROP TABLE IF EXISTS temp;
CREATE TABLE IF NOT EXISTS temp (cik varchar(13), data jsonb);
CREATE TABLE IF NOT EXISTS facts (
	cik varchar(13) not null primary key,
	data jsonb
);

DO $$
BEGIN
	INSERT INTO facts (cik, data)
	values('%s', (select * from to_jsonb('%s'::JSONB)))
END $$;