import numpy as np
from matplotlib import pyplot as plt

figures = np.load("data/figures_test.npy")
arr = figures[2]

plt.imshow(arr, cmap='gray')
plt.show()