import numpy as np

if __name__ == "__main__":
    matrix = np.array([[0.05, 0.05],
                       [0.85, 0.05]], dtype='d')
    indexes = [(i, j) for i in range(matrix.shape[0]) for j in range(matrix.shape[1])]
    flat_matrix = matrix.flatten()
    chosen_indices = np.random.choice(len(flat_matrix), size=10, p=flat_matrix)
    chosen_scores = [indexes[i] for i in chosen_indices]    
    print(chosen_scores)
