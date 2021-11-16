HEADER_NAMES = ["Lauf Nr.", "Project Id", "Firma", "Bereich",
                "Geschlecht", "Vorname", "Nachname", "Adresse FA",
                "PLZ FA", "Ort FA", "Telefon", "Mobil", "Fax", "Auftragsort",
                "Auftragsdatum", "LFN", "OVERFLOW", "OVERFLOW_2"]

COLS_TO_DISPLAY_NAME = {    "projectId"  : "Project Id",
                            "firma"      : "Firma",
                            "bereich"    : "Bereich",
                            "geschlecht" : "Anrede",
                }

IS_INT_TYPE  = ["laufNr", "projectId", "PLZ_FA", "lfn"]
IS_DATE_TYPE = ["auftragsdatum"]
IS_TEL_TYPE  = ["tel_1"]

COL_NAMES_TO_OPTIONS = { "geschlecht" : ["Herr", "Frau", "z.H. Herr",
                                            "z.H. Frau", "Herr und Frau", "N/A"],
                         "placeholder" : ["placeholder_A", "placeholder_B"]
                        }
