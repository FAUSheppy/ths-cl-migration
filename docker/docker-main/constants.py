HEADER_NAMES = ["Lauf Nr.", "Project Id", "Firma", "Bereich",
                "Geschlecht", "Vorname", "Nachname", "Adresse FA",
                "PLZ FA", "Ort FA", "Telefon", "Mobil", "Fax", "Auftragsort",
                "Auftragsdatum", "LFN", "OVERFLOW", "OVERFLOW_2"]

COLS_TO_DISPLAY_NAME = {    "projectId"  : "Project Id",
                            "firma"      : "Firma",
                            "bereich"    : "Bereich",
                            "geschlecht" : "Anrede",
                            "vorname"    : "Vorname",
                            "nachname"   : "Nachname",
                            "plz_fa"     : "PLZ FA",
                            "adresse_FA" : "Adresse FA",
                            "adresse_fa" : "Adresse FA",
                            "ort_FA"     : "Ort FA",
                            "ort_fa"     : "Ort FA",
                            "tel_1"      : "Festnetz",
                            "mobil"      : "Mobil",
                            "fax"        : "Fax",
                            "auftragsort": "Auftragsort",
                            "auftragsdatum" : "Auftragsdatum",
                            "lfn"        : "LFN",
                            "laufNr"     : "Lauf Nr.",
                            "laufnr"     : "Lauf Nr."
                }

IS_INT_TYPE  = ["laufNr", "projectId", "PLZ_FA", "lfn", "plz_fa"]
IS_DATE_TYPE = ["auftragsdatum"]
IS_TEL_TYPE  = ["tel_1"]
IS_TEMPLATE_IDENT = [ "firma", "bereich", "geschlecht", "vorname", "nachname",
                        "adresse_fa", "ort_fa", "tel_1", "mobil", "fax"]

COL_NAMES_TO_OPTIONS = { "geschlecht" : ["Herr", "Frau", "z.H. Herr",
                                            "z.H. Frau", "Herr und Frau", "N/A"],
                         "placeholder" : ["placeholder_A", "placeholder_B"]
                        }

MS_WORD_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

DB_DATE_FORMAT = "%d.%m.%Y"
HTML_DATE_FORMAT = "%Y-%m-%d"

COLS_IGNORE_LIST = ["_sa_instance_state", "date_parsed"]

BLACK_LIST_KEYWORDS = ["gmbh", "hausverwaltung", "i.v."]
WARNING_PATH_EXISTS_NO_CHANGE = '''Eine Datei oder ein Ordner mit diesem Name existiert bereits.<br>Es wurden keine Änderungen vorgenommen.<br>Pfad: {}'''
WARNING_SAMBA_TICKET_EXPIRED = "Fehler, wahrscheinlich Samba-Ticket abgelaufen, versuchen sie es in 5-10s nochmal"
WARNING_INTERNAL_SERVER_ERROR = "Interner Serverfehler"
