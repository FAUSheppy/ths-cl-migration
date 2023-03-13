TRIGGER_FOR_SEARCHABLE_STRING_1 = '''
    CREATE TRIGGER IF NOT EXISTS populate_searchable_insert
        AFTER INSERT ON contract_locations
    BEGIN
        INSERT INTO search_helper VALUES (
            NEW.projectid, ( 
                                COALESCE(NEW.firma,'')
                             || COALESCE(NEW.projectid,'')
                             || COALESCE(NEW.bereich,'')
                             || COALESCE(NEW.vorname,'')
                             || COALESCE(NEW.nachname,'')
                             || COALESCE(NEW.adresse_fa,'')
                             || COALESCE(NEW.plz_fa,'')
                             || COALESCE(NEW.ort_fa,'')
                             || COALESCE(NEW.tel_1,'')
                             || COALESCE(NEW.mobil,'')
                             || COALESCE(NEW.fax,'')
                             || COALESCE(NEW.auftragsort,'')
                             || COALESCE(NEW.auftragsdatum,'')
                          )
        );
    END;'''

TRIGGER_FOR_SEARCHABLE_STRING_2 = '''
    CREATE TRIGGER IF NOT EXISTS populate_searchable_update
        AFTER UPDATE ON contract_locations
    BEGIN
        UPDATE search_helper
            SET fullstring = (
                                COALESCE(NEW.firma,'')
                             || COALESCE(NEW.projectid,'')
                             || COALESCE(NEW.bereich,'')
                             || COALESCE(NEW.vorname,'')
                             || COALESCE(NEW.nachname,'')
                             || COALESCE(NEW.adresse_fa,'')
                             || COALESCE(NEW.plz_fa,'')
                             || COALESCE(NEW.ort_fa,'')
                             || COALESCE(NEW.tel_1,'')
                             || COALESCE(NEW.mobil,'')
                             || COALESCE(NEW.fax,'')
                             || COALESCE(NEW.auftragsort,'')
                             || COALESCE(NEW.auftragsdatum,'')
                            )
            WHERE projectid = NEW.projectid;
    END;'''

DOCUMENT_VIEW = '''
    CREATE OR REPLACE VIEW ths_word_helper AS
    SELECT
        cl.lfn,
        cl.projectid,
        cl.firma,
        cl.bereich,
        cl.geschlecht,
        cl.vorname,
        cl.nachname,
        cl.adresse_fa,
        cl.plz_fa,
        cl.ort_fa,
        cl.tel_1,
        cl.mobil,
        cl.fax,
        cl.auftragsort,
        cl.auftragsdatum,
        cl.date_parsed,
        SUBSTRING((cl.projectid)::character varying(30) FROM 1 FOR 4) AS projectid_short,
        SUBSTRING((cl.projectid)::character varying(30) FROM 5 FOR 4) AS projectid_lfn,
        REGEXP_REPLACE(
            REPLACE(
                REGEXP_REPLACE(
                    REGEXP_REPLACE(
                        ad.dates,
                        '(.+)',
                        ',\1'
                    ),
                    '(.*),', '\1 und '
                ),
                ',', ', '
            ),
            '$und', ' und'
        ) AS additional_dates
    FROM 
        contract_locations AS cl
        LEFT JOIN additional_dates AS ad ON cl.projectid = ad.projectid; 
    ;
'''
