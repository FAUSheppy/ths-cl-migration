TRIGGER_FOR_SEARCHABLE_STRING_1 = '''
    CREATE TRIGGER IF NOT EXISTS populate_searchable_insert
        AFTER INSERT ON contract_locations
    BEGIN
        INSERT INTO searchHelper VALUES (
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
    END;'''

TRIGGER_FOR_SEARCHABLE_STRING_2 = '''
    CREATE TRIGGER IF NOT EXISTS populate_searchable_update
        AFTER UPDATE ON contract_locations
    BEGIN
        UPDATE searchHelper
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
    END;'''
