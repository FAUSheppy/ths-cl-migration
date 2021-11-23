TRIGGER_FOR_SEARCHABLE_STRING_1 = '''
    DROP TRIGGER IF EXISTS populate_searchable_insert_trigger on "contract_locations";
    CREATE OR REPLACE FUNCTION populate_searchable_insert()
        RETURNS TRIGGER
        LANGUAGE PLPGSQL
    AS $$
    BEGIN
        INSERT INTO "searchHelper" VALUES (
            NEW.projectId, ( 
                                COALESCE(NEW.firma,'')
                             || COALESCE(NEW.projectId,'')
                             || COALESCE(NEW.bereich,'')
                             || COALESCE(NEW.vorname,'')
                             || COALESCE(NEW.nachname,'')
                             || COALESCE(NEW.adresse_FA,'')
                             || COALESCE(NEW.PLZ_FA,'')
                             || COALESCE(NEW.ort_FA,'')
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
        FOR EACH STATEMENT
        EXECUTE PROCEDURE populate_searchable_insert();
'''

TRIGGER_FOR_SEARCHABLE_STRING_2 = '''
    DROP TRIGGER IF EXISTS populate_searchable_update_trigger on "contract_locations";
    CREATE OR REPLACE FUNCTION populate_searchable_update()
        RETURNS TRIGGER
        LANGUAGE PLPGSQL
    AS $$
    BEGIN
        UPDATE "searchHelper"
            SET fullString = (
                                COALESCE(NEW.firma,'')
                             || COALESCE(NEW.projectId,'')
                             || COALESCE(NEW.bereich,'')
                             || COALESCE(NEW.vorname,'')
                             || COALESCE(NEW.nachname,'')
                             || COALESCE(NEW.adresse_FA,'')
                             || COALESCE(NEW.PLZ_FA,'')
                             || COALESCE(NEW.ort_FA,'')
                             || COALESCE(NEW.tel_1,'')
                             || COALESCE(NEW.mobil,'')
                             || COALESCE(NEW.fax,'')
                             || COALESCE(NEW.auftragsort,'')
                             || COALESCE(NEW.auftragsdatum,'')
                            )
            WHERE projectId = NEW.projectId;
            RETURN NEW;
    END;
    $$;
    CREATE TRIGGER populate_searchable_update_trigger
        AFTER INSERT ON contract_locations
        FOR EACH STATEMENT
        EXECUTE PROCEDURE populate_searchable_update();
    '''
