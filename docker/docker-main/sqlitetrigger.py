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
