import pandas as pd
from sklearn.model_selection import train_test_split

# Step 1: Load Fake and True news
fake = pd.read_csv("data/Fake.csv")
true = pd.read_csv("data/True.csv")

# Step 2: Add labels
fake["label"] = 0
true["label"] = 1

# Step 3: Keep only title + label
fake = fake[["title", "label"]]
true = true[["title", "label"]]

# Step 4: Combine datasets
data = pd.concat([fake, true], ignore_index=True)
data = data.sample(frac=1, random_state=42).reset_index(drop=True)

# Step 5: Clean data
data.dropna(inplace=True)
data = data.drop_duplicates(subset="title")

print("Dataset shape:", data.shape)
print(data.head())

# Step 6: Split into train/test
train_texts, test_texts, train_labels, test_labels = train_test_split(
    data["title"], data["label"], test_size=0.2, random_state=42
)
