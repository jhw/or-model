def mean(X):
    return sum(X)/len(X) if X != [] else 0

def variance(X):
    m = mean(X)
    return sum([(x-m)**2 for x in X])

def std_deviation(X):
    return variance(X)**0.5

if __name__ == "__main__":
    pass
