from Ch3 import human_v_bot, bot_v_bot


def main():
    x = int(input("Welcome to The Game of Go\n\nOptions:\n1: Player v Bot\n2. Bot v Bot\nYour selection? "))
    while x > 2 or x < 1:
        print("\nInvalid Selection Please Try Again")
        x = int(input("Your selection? "))
    y = int(input("\nWhat board size would you like (Odd number between 5 and 19)?\nYour Selection? "))
    while y > 19 or y < 5 or y % 2 is 0:
        print("\nInvalid Selection Please Try Again")
        y = int(input("Your selection? "))
    if x == 1:
        print("\nStarting Player v Bot\nEnter your selections in the form of [letter][number]")
        human_v_bot.main(y)
    else:
        print("\nStarting Bot v Bot")
        bot_v_bot.main(y)


if __name__ == '__main__':
    main()
