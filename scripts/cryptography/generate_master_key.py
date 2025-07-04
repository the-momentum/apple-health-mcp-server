from cryptography.fernet import Fernet


def main():
    print(Fernet.generate_key())


if __name__ == "__main__":
    main()
