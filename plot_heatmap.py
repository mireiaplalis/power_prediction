import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.cm as cm

data = np.load("./data/flow-matrices.npy")

i = 6

data_i = data[i].squeeze()

plt.figure()
sns.heatmap(-data[-1].squeeze(), xticklabels=False, yticklabels=False, cmap=cm.gray)
plt.savefig(f"./data/example_{i}_heatmap.png")