import pickle
from collections import UserDict
from datetime import datetime, timedelta, date

SAVE_FILE = "addressbook.pkl"

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    pass

class Phone(Field):
    def __init__(self, value):
        if not (value.isdigit() and len(value) == 10):
            raise ValueError("The phone number must contain exactly 10 digits")
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value):
        try:
            parsed_date = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(parsed_date)

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone: str):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone: str):
        phone_obj = self.find_phone(phone)
        if phone_obj:
            self.phones.remove(phone_obj)

    def edit_phone(self, old_phone: str, new_phone: str):
        phone_obj = self.find_phone(old_phone)
        if not phone_obj:
            raise ValueError("Old phone number not found.")
        new_phone_obj = Phone(new_phone)
        phone_obj.value = new_phone_obj.value

    def find_phone(self, phone: str):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_birthday(self, birthday_str: str):
        self.birthday = Birthday(birthday_str)

    def days_to_birthday(self):
        if not self.birthday:
            return None
        today = date.today()
        next_birthday = self.birthday.value.replace(year=today.year)
        if next_birthday < today:
            next_birthday = next_birthday.replace(year=today.year + 1)
        return (next_birthday - today).days

    def __str__(self):
        phones_str = '; '.join(str(phone) for phone in self.phones) if self.phones else "No phones"
        birthday_str = self.birthday.value.strftime("%d.%m.%Y") if self.birthday else "No birthday"
        return f"Contact name: {self.name.value}, phones: {phones_str}, birthday: {birthday_str}"

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self, days=7):
        today = date.today()

        def adjust_for_weekend(d):
            if d.weekday() == 5:
                return d + timedelta(days=2)
            elif d.weekday() == 6:
                return d + timedelta(days=1)
            return d

        upcoming = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            bday = record.birthday.value
            next_birthday = bday.replace(year=today.year)
            if next_birthday < today:
                next_birthday = next_birthday.replace(year=today.year + 1)

            next_birthday = adjust_for_weekend(next_birthday)
            days_diff = (next_birthday - today).days

            if 0 <= days_diff <= days:
                congratulation_date_str = next_birthday.strftime("%d.%m.%Y")
                upcoming.append({
                    "name": record.name.value,
                    "congratulation_date": congratulation_date_str
                })

        return upcoming

    def __str__(self):
        if not self.data:
            return "Address book is empty."
        return "\n".join(str(record) for record in self.data.values())


def save_data(book, filename=SAVE_FILE):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename=SAVE_FILE):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return f"Error: {str(e)}"
        except KeyError:
            return "Error: Contact not found"
        except IndexError:
            return "Error: Missing arguments. Please provide enough information."
    return inner

def parse_input(user_input):
    parts = user_input.strip().split()
    if not parts:
        return "", []
    cmd = parts[0].lower()
    args = parts[1:]
    return cmd, args

@input_error
def add_contact(args, book):
    name, phone = args[0], args[1]
    record = book.find(name)
    if record is None:
        record = Record(name)
        record.add_phone(phone)
        book.add_record(record)
        return f"Added contact {name} with phone {phone}"
    else:
        record.add_phone(phone)
        return f"Added phone {phone} to contact {name}"

@input_error
def change_contact(args, book):
    name, old_phone, new_phone = args
    record = book.find(name)
    if not record:
        return f"Contact with name: {name} not found"
    record.edit_phone(old_phone, new_phone)
    return f"Phone number for {name} changed from {old_phone} to {new_phone}."

@input_error
def show_phone(args, book):
    name = args[0]
    record = book.find(name)
    if not record:
        return f"Contact with name: {name} not found"
    phones = ', '.join(str(phone) for phone in record.phones) if record.phones else "No phones"
    return f"Phone number for {name}: {phones}"

@input_error
def show_all(book):
    if not book.data:
        return "Contact list is empty"
    return str(book)

@input_error
def add_birthday(args, book: AddressBook):
    name = args[0]
    birthday_str = args[1]
    record = book.find(name)
    if not record:
        return f"Contact with name '{name}' not found"
    record.add_birthday(birthday_str)
    return f"Date of birth for {name} added: {birthday_str}"

@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    if not record:
        return f"Contact with name {name} not found"
    if not record.birthday:
        return f"The contact {name} doesn’t have a birthday"
    return f"Birthday for {name}: {record.birthday.value.strftime('%d.%m.%Y')}"

@input_error
def birthdays(args, book):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays this week"
    result = "Upcoming birthdays:\n"
    for user in upcoming:
        result += f"{user['name']}: {user['congratulation_date']}\n"
    return result.strip()

def main():
    book = load_data()  # <--- завантаження даних при запуску
    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)  # <--- збереження даних перед виходом
            print("Address book saved. Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            result = add_contact(args, book)
            print(result)

        elif command == "change":
            result = change_contact(args, book)
            print(result)

        elif command == "phone":
            result = show_phone(args, book)
            print(result)

        elif command == "all":
            result = show_all(book)
            print(result)

        elif command == "add-birthday":
            result = add_birthday(args, book)
            print(result)

        elif command == "show-birthday":
            result = show_birthday(args, book)
            print(result)

        elif command == "birthdays":
            result = birthdays(args, book)
            print(result)

        else:
            print("Unknown command. Try: add, change, phone, all, add-birthday, show-birthday, birthdays, exit")

if __name__ == "__main__":
    main()
