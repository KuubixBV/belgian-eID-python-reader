from reader import eIDReader

# Create eID object using name of card reader - I am using the "Cherry ST-1144" card reader! Make sure to use a card reader that can use CCID using protocol T0, T1!
eID = eIDReader("cherry")
if eID.read_card():

    # Data received
    print("Read OK")

    # Print last read card content to screen
    print(eID.get_last_read_eID_contact().to_json())

else:
    print("Error")