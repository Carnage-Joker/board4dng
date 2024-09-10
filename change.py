# Open the input file in read mode and the output file in write mode
with open('bad_words.txt', 'r') as infile, open('new_bad.txt', 'w') as outfile:
    # Read the content of the input file
    content = infile.read()

    # Remove quotes and split the string by commas
    words = content.replace('"', '').replace(',', '').split()

    # Write each word on a new line in the output file
    for word in words:
        outfile.write(word.strip() + '\n')
