from collections import Counter
from textblob import TextBlob

a = TextBlob(
    "alma alma barack"
)

print(Counter(a.word_counts))
