# Reading Belgian eID cards using UWP with python

This python package can read Belgian eID cards without a middleware software installed. This is achieved by talking directly to the chip. (DF01/4031) Please use a **smart** card reader e.g. "A contact smart card reader is an electronic device that physically connects to an integrated circuit in a smart card, supplies the circuit in the card with electricity, and uses communications protocols to read data from the card." - Wikipedia. This class uses the pyscard module https://pyscard.sourceforge.io/. I am using a 'Cherry ST-1144'. I have not tested any other smart card readers.

## 1. Installation

Clone this repo
```bash
git clone https://github.com/KuubixBV/belgian-eID-python-reader.git
```

Change directory
```bash
cd ./belgian-eID-python-reader
```

Install pyscard module
```bash
python -m pip install pyscard 
```

## 2. Usage

Import the reader into your project

```python
from reader import eIDReader
```

Create a new object of the class, this will find the first USB device that is supported by pyscard.

```python
eID = eIDReader()
```

Alternatively, you can create a new object of the class with the brand name of the card reader. This will find the first card reader of the given brand.

```python
eID = eIDReader("cherry")
```

Each read method will return true if the read was successful or throws an exception. You can use the following read methods:

```python
eID.read_address() # Reads the address
eID.read_photo() # Reads photo
eID.read_registre_national() # Reads all other ID data
```

If you want to read everything of the eID you can use:

```python
eID.read_card() # Reads the entire card
```

Like stated before, every read method will either return true or throw an exception. If the read method returned true, you can receive the data in 2 ways.

Returning the data with the get_last_read method:

```python
eID_contact = eID.get_last_read() # Returns last read eIDContact object
```

Returning all data by checking out the eID_contacts array:

```python
eID_contacts = eID.eID_contacts # Returns all read eIDContact objects
```

Each eIDContact object consists of the following data:

```python
# Registre national (RN) data
eID_contact.card_number
eID_contact.chip_number
eID_contact.card_validity_begin # Data is unix timestamp
eID_contact.card_validity_end # Data is unix timestamp
eID_contact.card_delivery_municipality
eID_contact.national_number
eID_contact.name
eID_contact.two_first_given_names
eID_contact.first_letter_of_third_name
eID_contact.nationality
eID_contact.birthplace
eID_contact.birthdate # Data is unix timestamp
eID_contact.sex # "M" or "F" -> simplified
eID_contact.noble_condition
eID_contact.document_type # "Belgian citizen" or "European community citizen" or "None European community citizen" or "Bootstrap card" or "Abilitation/machtigings card"
eID_contact.white_cane # True or False
eID_contact.yellow_cane # True or False
eID_contact.extended_minority # True or False
eID_contact.hash_photo

# Address data
eID_contact.street
eID_contact.zip_code
eID_contact.municipality
eID_contact.country # Always returns "België"

# Photo data
eID_contact.photo
```

The eIDContact object has the following methods to return data either as a dictionary or as json

```python
contact_as_json = eID_contact.to_json()
contact_as_dictionary = eID_contact.to_dict()
```

See example.py for a working demo.
