TRIGGER_FOR_SEARCHABLE_STRING_1 = '''
    DROP TRIGGER IF EXISTS populate_searchable_insert_trigger on "contract_locations";
    CREATE OR REPLACE FUNCTION populate_searchable_insert()
        RETURNS TRIGGER
        LANGUAGE PLPGSQL
    AS $$
    BEGIN
        INSERT INTO "search_helper" VALUES (
            NEW.projectid, ( 
                                COALESCE(NEW.firma,'')
                             || COALESCE(NEW.projectid::text,'')
                             || COALESCE(NEW.bereich,'')
                             || COALESCE(NEW.vorname,'')
                             || COALESCE(NEW.nachname,'')
                             || COALESCE(NEW.adresse_fa,'')
                             || COALESCE(NEW.plz_fa::text,'')
                             || COALESCE(NEW.ort_fa,'')
                             || COALESCE(NEW.tel_1,'')
                             || COALESCE(NEW.mobil,'')
                             || COALESCE(NEW.fax,'')
                             || COALESCE(NEW.auftragsort,'')
                             || COALESCE(NEW.auftragsdatum,'')
                          )
        );
        RETURN NEW;
    END;
    $$;
    CREATE TRIGGER populate_searchable_insert_trigger
        AFTER INSERT ON contract_locations
        FOR EACH ROW
        EXECUTE PROCEDURE populate_searchable_insert();
'''

TRIGGER_FOR_SEARCHABLE_STRING_2 = '''
    DROP TRIGGER IF EXISTS populate_searchable_update_trigger on "contract_locations";
    CREATE OR REPLACE FUNCTION populate_searchable_update()
        RETURNS TRIGGER
        LANGUAGE PLPGSQL
    AS $$
    BEGIN
        UPDATE "search_helper"
            SET fullstring = (
                                COALESCE(NEW.firma,'')
                             || COALESCE(NEW.projectid::text,'')
                             || COALESCE(NEW.bereich,'')
                             || COALESCE(NEW.vorname,'')
                             || COALESCE(NEW.nachname,'')
                             || COALESCE(NEW.adresse_fa,'')
                             || COALESCE(NEW.plz_fa::text,'')
                             || COALESCE(NEW.ort_fa,'')
                             || COALESCE(NEW.tel_1,'')
                             || COALESCE(NEW.mobil,'')
                             || COALESCE(NEW.fax,'')
                             || COALESCE(NEW.auftragsort,'')
                             || COALESCE(NEW.auftragsdatum,'')
                            )
            WHERE projectid = NEW.projectid;
            RETURN NEW;
    END;
    $$;
    CREATE TRIGGER populate_searchable_update_trigger
        AFTER UPDATE ON contract_locations
        FOR EACH ROW
        EXECUTE PROCEDURE populate_searchable_update();
    '''
