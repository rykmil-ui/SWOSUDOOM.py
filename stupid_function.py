import random

def coin_flip(trials):
    heads = 0
    tails = 0

    for flip in range(trials):
        coin = random.randint(1, 2)

        if coin == 1:
            heads += 1
        else:
            tails += 1

    print("Heads:", heads)
    print("Tails:", tails)


def dice_roll(trials):
    results = [0, 0, 0, 0, 0, 0]

    for roll in range(trials):
        dice = random.randint(1, 6)
        results[dice - 1] += 1

    print("1:", results[0])
    print("2:", results[1])
    print("3:", results[2])
    print("4:", results[3])
    print("5:", results[4])
    print("6:", results[5])


print("What would you like to do?")
print("1. Flip a coin")
print("2. Roll a dice")

choice = input("Enter 1 or 2: ")
trials = int(input("How many trials do you want? "))

if choice == "1":
    coin_flip(trials)

elif choice == "2":
    dice_roll(trials)

else:
    print("Invalid choice.")