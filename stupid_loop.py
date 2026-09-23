import random

heads = 0
tails = 0

for flip in range(1000000):
    coin = random.randint(1, 2)

    if coin == 1:
        heads += 1
    else:
        tails += 1

print("Heads:", heads)
print("Tails:", tails)