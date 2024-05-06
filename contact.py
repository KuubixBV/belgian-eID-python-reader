import datetime
import base64
import json
import time

class eIDContact:

    # Registre national (RN) data
    card_number = ""
    chip_number = ""
    card_validity_begin = ""
    card_validity_end = ""
    card_delivery_municipality = ""
    national_number = ""
    name = ""
    two_first_given_names = ""
    first_letter_of_third_name = ""
    nationality = ""
    birthplace = ""
    birthdate = ""
    sex = ""
    noble_condition = ""
    document_type = ""
    white_cane = 0
    yellow_cane = 0
    extended_minority = 0
    hash_photo = ""

    # Address data
    street = ""
    zip_code = ""
    municipality = ""
    country = "België"

    # Photo data
    photo = ""

    # Created and updated
    _created = datetime.datetime.now().timestamp()
    updated = datetime.datetime.now().timestamp()

    # Construct
    def __init__(self, card_number):
        self.card_number = card_number
    
    # Methods

    ## Saves the current contact - we use a dictonary to save everything
    def _save(self, data):

        # Loop over all values and set using setattr
        for key, value in data.items():

            # Convert spaces in keys to underscores to match the class attribute names
            attribute_name = key.replace(" ", "_")

            # Check if key is birthdate
            if attribute_name == "birthdate":
                value = self._birthdate_to_timestamp(value)

            # Check if key is date like
            if attribute_name == "card_validity_begin" or attribute_name == "card_validity_end":
                value = self._date_to_timestamp(value)

            # Check for SEX (why do they store the F versions in 3 languages????)
            if attribute_name == "sex":
                value = "M" if value == "M" else "F"

            # Check for document_type
            if attribute_name == "document_type":
                value = self._document_type_to_string(value)

            # Check for status code
            if attribute_name == "special_status":
                value = int(value)
                self.white_cane = (value & 1) != 0
                self.extended_minority = (value & 2) != 0
                self.yellow_cane = (value & 4) != 0
            else:
                # Check if the attribute exists in the class before setting it
                if hasattr(self, attribute_name):

                    # Check if type is bytearray
                    if isinstance(value, (bytes, bytearray)):
                        # Encode and decode to convert bytes to string for JSON serialization
                        value = base64.encodebytes(value).decode('utf-8').strip()
                    setattr(self, attribute_name, value)
                else:
                    raise Exception(f"Attribute '{attribute_name}' does not exist!")

        self.updated = datetime.datetime.now().timestamp()

    ## Date convert to timestamp
    def _date_to_timestamp(self, date_str):

        # Parse the date string
        day, month, year = map(int, date_str.split('.'))
        date = datetime.datetime(year, month, day)
        
        # Convert the datetime object to a UNIX timestamp
        timestamp = int(time.mktime(date.timetuple()))
        
        return timestamp

    ## Calculate document type as string
    def _document_type_to_string(self, document_type):

        # Dictionary to map
        document_mapping = {
            "1": "Belgian citizen",
            "2": "European community citizen",
            "3": "None European community citizen",
            "7": "Bootstrap card",
            "8": "Abilitation/machtigings card"
        }

        return document_mapping.get(document_type, 0)

    ## BirthDate convert to timestamp
    def _birthdate_to_timestamp(self, birthdate_str):

        # Dictionary to map the month abbreviations to month numbers
        month_mapping = {
            "JAN": 1, "FEV": 2, "FEB": 2, "MARS": 3, "MAAR": 3, "MÄR": 3,
            "AVR": 4, "APR": 4, "MAI": 5, "MEI": 5, "JUIN": 6, "JUN": 6,
            "JUIL": 7, "JUL": 7, "AOUT": 8, "AUG": 8, "SEPT": 9, "SEP": 9,
            "OCT": 10, "OKT": 10, "NOV": 11, "DEC": 12, "DEZ": 12
        }

        # Extract day, month as string, and year
        split_date = birthdate_str.split()
        day = int(split_date[0])
        month_str = split_date[1].upper()
        year = int(split_date[2])

        # Map the string month to a number
        month = month_mapping.get(month_str, 0)
        if month == 0:
            raise ValueError("Invalid month abbreviation in birthdate string")

        # Create a datetime object
        birthdate = datetime.datetime(year, month, day)
        timestamp = int(time.mktime(birthdate.timetuple()))
        
        return timestamp
        

    ## Resets the current contact
    def _reset(self, files = None):

        # Check if "RV" in files or None
        if "RV" in files or files == None:

            # Reset data for "RV"
            self.card_number = ""
            self.chip_number = ""
            self.card_validity_begin = ""
            self.card_validity_end = ""
            self.card_delivery_municipality = ""
            self.national_number = ""
            self.name = ""
            self.two_first_given_names = ""
            self.first_letter_of_third_name = ""
            self.nationality = ""
            self.birthplace = ""
            self.birthdate = ""
            self.sex = ""
            self.noble_condition = ""
            self.document_type = ""
            self.hash_photo = ""
            self.white_cane = 0
            self.yellow_cane = 0
            self.extended_minority = 0
    
        # Check if "ADDRESS" in files or None
        if "ADDRESS" in files or files == None:

            # Reset data for "ADDRESS"
            self.street = ""
            self.zip_code = ""
            self.municipality = ""

        # Check if "PHOTO" in files or None
        if "PHOTO" in files or files == None:

            # Reset data for "PHOTO"
            self.photo = ""

    # Returns the current object as a JSON object
    def to_json(self):
        return json.dumps(
            self.to_dict(),
            default=lambda o: o.__dict__, 
            sort_keys=True,
            ensure_ascii=False,
            indent=4)
    
    # Returns the current object as a DICT object
    def to_dict(self):
        #return { "name": self.two_first_given_names, "updated": datetime.datetime.fromtimestamp(self.updated).strftime('%d/%m/%Y %H:%M:%S') }
        return {key: getattr(self, key) for key in dir(self) if not key.startswith('_') and not callable(getattr(self, key))}
