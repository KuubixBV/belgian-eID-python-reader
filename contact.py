import datetime
import json
import base64

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
    birth_location = ""
    birth_date = ""
    sex = ""
    noble_condition = ""
    document_type = ""
    special_status = ""
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
            self.birth_location = ""
            self.birth_date = ""
            self.sex = ""
            self.noble_condition = ""
            self.document_type = ""
            self.special_status = ""
            self.hash_photo = ""
    
        # Check if "ADDRESS" in files or None
        if "ADDRESS" in files or files == None:

            # Reset data for "ADDRESS"
            self.street = ""
            self.zip_code = ""
            self.municipality = ""

        # Check if "PHOTO" in files or None
        if "ADDRESS" in files or files == None:

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
        return {key: getattr(self, key) for key in dir(self) if not key.startswith('_') and not callable(getattr(self, key))}
