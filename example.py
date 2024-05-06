from reader import eIDReader

# Method that keeps reading the card
def read_card():
    while eID.read_card():

        # Data received
        print("Read OK")

        # Print last read card content to screen
        print(eID.get_last_read().to_json())

        # Wait for user input to read next card
        input("Press Enter to read the next card...")

# Create eID object using name of card reader - I am using the "Cherry ST-1144" card reader! Make sure to use a card reader that can use CCID using protocol T0, T1!
eID = eIDReader("cherry")
while True:
    try:
        read_card()
    except Exception as e:
        print("Error reading card: ")
        print(e)
        input("Press Enter to try again...")
        pass

