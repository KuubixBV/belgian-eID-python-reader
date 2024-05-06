from smartcard.Exceptions import NoCardException
from smartcard.util import toHexString
from smartcard.System import readers
from contact import eIDContact
import time
import json

class eIDReader:

    # General used for class
    _reader = None
    _connection = None
    _name = None

    # Read eID contacts
    eID_contacts = []

    # Static values used for communication

    ## Basic read setup for ID-card - this will read the last selected file data on the chip
    _READ_COMMAND = [
                0x00, # CLA   
                0xB0, # INS  
                0x00, # P1  
                0x00, # P2
                0x00  # Length
    ]

    ## Select setup for selecting "Registre national" (RN) file on chip - this will select the "Registre national" file
    _SELECT_REGISTRE_NATIONAL = [
                0x00, # CLA 
                0xA4, # INS 
                0x08, # P1
                0x0C, # P2
                0x06, # Length
                0x3F, # Directory high (0xYY..)
                0x00, # Directory low (0x..YY)
                0xDF, # Subdirectory high (0xYY..)
                0x01, # Subdirectory low (0xYY..)
                0x40, # Registre national file high (0xYY..)
                0x31  # Registre national file low (0x..YY)
    ]

    ## Select setup for selecting "address" file on chip - this will select the "address" file
    _SELECT_ADDRESS = [  
                0x00, # CLA  
                0xA4, # INS 
                0x08, # P1
                0x0C, # P2
                0x06, # Length
                0x3F, # Directory high (0xYY..)
                0x00, # Directory low (0x..YY)
                0xDF, # Subdirectory high (0xYY..)
                0x01, # Subdirectory low (0xYY..)
                0x40, # Address file high (0xYY..)
                0x33  # Address file low (0x..YY)
    ]

    ## Select setup for selecting "Photo" file on chip - this will select the "Photo" file
    _SELECT_PHOTO = [  
            0x00, # CLA 
            0xA4, # INS 
            0x08, # P1
            0x0C, # P2
            0x06, # Length
            0x3F, # Directory high (0xYY..)
            0x00, # Directory low (0x..YY)
            0xDF, # Subdirectory high (0xYY..)
            0x01, # Subdirectory low (0xYY..)
            0x40, # Photo file high (0xYY..)
            0x35  # Photo file low (0x..YY)
    ]

    # Static values used for mapping tags and selecting encoding

    ## Mapping for "Address" file
    _ADDRESS_MAPPING = {
        1: { "name": "street", "encoding": "utf-8" },
        2: { "name": "zip_code", "encoding": "ascii" }, 
        3: { "name": "municipality", "encoding": "utf-8" },
    }

    ## Mapping for "Registre national" file
    _REGISTRE_NATIONAL_MAPPING = {
        1: { "name": "card number", "encoding": "ascii" },
        2: { "name": "chip number", "encoding": "" }, 
        3: { "name": "card validity begin", "encoding": "ascii" },
        4: { "name": "card validity end", "encoding": "ascii" },
        5: { "name": "card delivery municipality", "encoding": "utf-8" },
        6: { "name": "national number", "encoding": "ascii" },
        7: { "name": "name", "encoding": "utf-8" },
        8: { "name": "two first given names", "encoding": "utf-8" },
        9: { "name": "first letter of third name", "encoding": "utf-8" },
        10: { "name": "nationality", "encoding": "utf-8" },
        11: { "name": "birthplace", "encoding": "utf-8" },
        12: { "name": "birthdate", "encoding": "utf-8" },
        13: { "name": "sex", "encoding": "ascii" },
        14: { "name": "noble condition", "encoding": "utf-8" },
        15: { "name": "document type", "encoding": "ascii" },
        16: { "name": "special status", "encoding": "ascii" },
        17: { "name": "hash photo", "encoding": "" },
    }

    # Validate object before creating
    def __new__(cls, name = ""):
        obj = super().__new__(cls)
        obj._name = name
        obj._init_reader()
        return obj

    # Init the reader - this will create a new smartcard object
    def _init_reader(self):

        # Check what for reader should be looked for
        if self._name != "":
            reader = next((reader for reader in readers() if reader.name.lower().startswith(self._name.lower())), None)
            if not reader:
                raise Exception(f"Could not find card reader. Please make sure a card reader that starts with '{self._name.lower()}' is plugged in. The following card readers are found:\n{readers()}")
        else:
            if len(readers()) <= 0:
                raise Exception("Could not find card reader.")
            reader = readers()[0]

        # Disconnect current reader if a connection was made - a new card maybe inserted
        if self._connection:
            self._connection.disconnect()
        
        # Init reader on object
        self._reader = reader
        self._connection = reader.createConnection()
        self._connection.connect()

    # Check if the card is responding to a select
    def _select_and_validate(self, file = "RV", retry = 3):

        # Check if retry counter is done!
        if retry <= 0:
            raise Exception(f"The eID card reader is not responding - or no card is inserted.")

        # Try to select a file
        try:
            self._select(file)
        except:

            # Wait to try again
            time.sleep(0.25)

            # Reset the card - a new eID may has been inserted
            self._init_reader()

            # Read again
            self._select_and_validate(file, retry - 1)
        
        return True

    # Methods
    def get_last_read(self):
        if len(self.eID_contacts) <= 0:
            raise Exception(f"No eID contacts read yet - please read one first")
        
        # Get last read contact based on updated timestamp
        sorted_contacts = sorted(self.eID_contacts, key=lambda contact: contact.updated, reverse=True)
        return sorted_contacts[0]

    ## Selects the correct file for reading - returns true for success - raises exception for error
    def _select(self, file="RN"):
        selected_file = []
        match file.upper():
            case "RN":
                selected_file = self._SELECT_REGISTRE_NATIONAL
            case "ADDRESS":
                selected_file = self._SELECT_ADDRESS
            case "PHOTO":
                selected_file = self._SELECT_PHOTO
            case _:
                raise Exception("Select failed - value not allowed. Allowed values are RN|ADDRESS|PHOTO")

        # Transmit to chip in order to select file
        response, sw1, sw2 = self._transmit(selected_file)

        # Check if transmission was received and handled
        if not self._validate_transmit(sw1, sw2):
            raise Exception(f"Select failed - response code not expected. Expected code '0x900', returned code '{hex(sw1) + hex(sw2)[2:]}'")
        
        return True

    ## Transmits data to the current card reader (either selecting or retreiving data)
    def _transmit(self, data):
        return self._connection.transmit(data)

    ## Checks if the transmission was succesfull (response code should be 0x900)
    def _validate_transmit(self, sw1, sw2):
        return hex(sw1) + hex(sw2)[2:] == "0x900"
    
    # Reads all data from the current inserted card -  returns true for success - raises exception for error
    def read_card(self):
        self.read_registre_national()
        self.read_address()
        self.read_photo()
        return True

    ## Reads the "Registre national" file - returns true for success - raises exception for error
    def read_registre_national(self, selected_data = None):

        # Check selected_data and fill if empty also, select RN file before reading chip
        if not selected_data or len(selected_data) <= 0:
            selected_data = {mapping["name"] for mapping in self._REGISTRE_NATIONAL_MAPPING.values()}
        else:
            self._check_selected_data(selected_data, self._REGISTRE_NATIONAL_MAPPING)
        self._select_and_validate("RN")

        # Read selected file and create contact object
        response = self._read()
        self._crud_contact(response, selected_data, self._REGISTRE_NATIONAL_MAPPING)
        return True
    
    ## Reads the "Address" file - returns true for success - raises exception for error
    def read_address(self, selected_data = None):

        # First get the card_number before we can continue
        if not self.read_registre_national([ "card number" ]) or len(self.eID_contacts) <= 0:
             raise Exception(f"Read failed - could not read card number - something went wrong")
        card_number = self.get_last_read().card_number

        # Check selected_data and fill if empty also, select RN file before reading chip
        if not selected_data or len(selected_data) <= 0:
            selected_data = {mapping["name"] for mapping in self._ADDRESS_MAPPING.values()}
        else:
            self._check_selected_data(selected_data, self._ADDRESS_MAPPING)
        self._select_and_validate("ADDRESS")

        # Read selected file and create contact object
        response = self._read()
        self._crud_contact(response, selected_data, self._ADDRESS_MAPPING, card_number)
        return True
    
    # Reads the current selected file - returns data if success - raises exception for error
    def _read(self):

        # Since we do not know how much data we need to read - we first must read the chip with length 0
        # After doing so our sw2 will contain the length of our data
        _, sw1, sw2 = self._transmit(self._READ_COMMAND)

        # Check if length is returned - our sw1 should be "0x6C"
        if hex(sw1) != "0x6c":
            raise Exception(f"Select failed - response code not expected. Expected code '0x900', returned code '{hex(sw1) + hex(sw2)[2:]}'")
        
        # Create new read command depending on size
        _READ_COMMAND_with_length = self._READ_COMMAND.copy()
        _READ_COMMAND_with_length[len(_READ_COMMAND_with_length)-1] = sw2
        response, sw1, sw2 = self._transmit(_READ_COMMAND_with_length)

        # Check if transmission was received and handled
        if not self._validate_transmit(sw1, sw2):
            raise Exception(f"Read failed - response code not expected. Expected code '0x900', returned code '{hex(sw1) + hex(sw2)[2:]}'")

        return response

    ## Reads the "Photo" file - returns true for success - raises exception for error
    def read_photo(self):

        # First get the card_number before we can continue
        if not self.read_registre_national([ "card number" ]) or len(self.eID_contacts) <= 0:
             raise Exception(f"Read failed - could not read card number - something went wrong")
        card_number = self.get_last_read().card_number
        self._select_and_validate("PHOTO")

        # Loop over file to retreive in 256 byte chunks
        photo = []
        offset = 0
        length = 256
        while length > 0:

            # Convert offset to hex and extract last two characters
            offset_hex = hex(offset)[2:].zfill(4)
            p1_hex = offset_hex[:2]
            p2_hex = offset_hex[2:]
            file = [  
                    0x00, # CLA
                    0xB0, # INS
                    int(p1_hex, 16), # P1
                    int(p2_hex, 16), # P2
                    length # LENGTH
            ]

            # Get response for file for chunk 
            response, sw1, sw2 = self._transmit(file)

            # Check if photo is complete
            photo_validated = self._validate_photo(response)
            if photo_validated:
                photo += response
                self._crud_contact({ "photo": bytearray(photo) }, None, None, card_number)
                return True
            
            # Photo not complete, change offset or length of data
            if(len (response) <= 0 and not photo_validated):
                length -= 1
            else:
                offset += 256
                photo += response

        # Error
        raise Exception("Read failed - could not read photo - something went wrong")

    # A JPG should end with a certain marker (FFD9) - returns true if FFD9 - false if not
    def _validate_photo(self, data):
        if len(data) >= 2:
            return data[len(data) - 2] == 255 and data[len(data) - 1] == 217
        return False

    # Creates or updates a eID contact after reading the data - returns data if success - raises exception for error
    def _crud_contact(self, data, selected_data, mapping, card_number = None ):

        # If card_number is not set, this means we have a RN read
        # We should first get the RN before continuing
        if not card_number:
            card_number = self._get_card_number(data, mapping)["card number"]
        
        # Check if card_number has value
        if not card_number:
            raise Exception("Could not get card_number - something went wrong")

        # Check if contact exists with card_number - if so, update - else create
        contact = self._find_contact(card_number)
        if not contact:
            contact = eIDContact(card_number)
            contact._save(self._decode_data(data, mapping, selected_data))
            self.eID_contacts.append(contact)
        else:
            contact._save(self._decode_data(data, mapping, selected_data))

        return True

    # Tries to find a contact with card_number - returns contact object if found - false if not found
    def _find_contact(self, card_number):
        for contact in self.eID_contacts:
            if contact.card_number == card_number:
                return contact
        return False

    # Used to parse the card_number from the data
    def _get_card_number(self, data, mapping):
        
        # Create new dictonary where ID = 1 so we get the mapping for the card_number
        filtered_mapping = {k: v for k, v in mapping.items() if k == 1}
        return self._decode_data(data, filtered_mapping)
    
    # Decodes all data
    def _decode_data(self, data, mapping, selected_data = None):

        # Check if no mapping needed (mapping happend in other method like 'read_photo')
        if mapping == None:
            return data

        # Set locals
        pointer = 0
        response = {}
        loops = 0

        # Convert original data to bytearray - cause python likes intarrays more ;-)
        data = bytearray(data)

        # Loop over data
        while loops < len(mapping):

            # Get current mapping and data length
            mapping_object = mapping[data[pointer]]
            key = mapping_object["name"]
            pointer += 1
            length = data[pointer]
            pointer += 1

            # Get value and encode following the mapped encoding - if no encoding use hex
            if mapping_object["encoding"]:
                value = data[pointer:pointer + length].decode(mapping_object["encoding"])
            else:
                value = data[pointer:pointer + length].hex()
            pointer += length

            # Create key/value pair if in selected_data or if none
            if selected_data == None or key in selected_data:
                response[key] = value
            loops += 1
        
        return response

    ## Check if selected_data is valid - returns true for valid - raises exception for invalid
    def _check_selected_data (self, selected_data, mappings):

            # Extract all possible 'name' keys from mapping
            valid_keys = {mapping["name"] for mapping in mappings.values()}

            # Find any keys in selected_data that are not in the valid_keys set
            invalid_keys = {key for key in selected_data if key not in valid_keys}
            
            if invalid_keys:
                # If there are invalid keys, raise an exception
                allowed_keys_str = ", ".join(valid_keys)
                invalid_keys_str = ", ".join(invalid_keys)
                raise ValueError(f"Invalid keys found: {invalid_keys_str}. Allowed keys are: {allowed_keys_str}.")
            
            return True