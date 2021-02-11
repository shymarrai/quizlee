txt = input()

words = txt.split()

longger, cont = 0,0

for letter in range(len(words)):

    if len(words[letter]) > longger:
        cont = letter
        longger = len(words[letter])
    else:
        continue

print(words[cont])

#your code goes here
