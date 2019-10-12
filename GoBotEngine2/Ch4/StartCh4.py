from Ch4 import variable_go


def main():
    x = int(input("Welcome to The Game of Go\n\nOptions:\n1: MCTS\n2. Alpha-Beta\n3. Pruned\nYour selection? "))
    while x > 3 or x < 1:
        print("\nInvalid Selection Please Try Again")
        x = int(input("Your selection? "))
    y = int(input("\nWhat board size would you like (Odd number between 5 and 19)?\nYour Selection? "))
    while y > 19 or y < 5 or y % 2 is 0:
        print("\nInvalid Selection Please Try Again")
        y = int(input("Your selection? "))
    print("\nStarting Game")
    variable_go.main(y, x)


if __name__ == '__main__':
    main()
