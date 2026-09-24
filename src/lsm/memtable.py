deleted = object()

class Memtable:
    def __init__(self):
        self.data = []

    def put(self, key, val):
        for i in range(len(self.data)):
            if self.data[i][0] > key:
                self.data.insert(i, [key, val])
                break
            if self.data[i][0] == key:
                self.data[i][1] = val
                break
        else:
            self.data.append([key, val])

    def get(self, key):
        low, high = 0, len(self.data) - 1
        while(low <= high):
            mid = (low + high) // 2
            if self.data[mid][0] == key:
                if self.data[mid][1] == deleted:
                    return deleted
                else:
                    return self.data[mid][1]
            if self.data[mid][0] < key: low = mid + 1
            else: high = mid - 1
        return None

    def delete(self, key):
        for i in range(len(self.data)):
            if self.data[i][0] > key:
                self.data.insert(i, [key, deleted])
                break
            if self.data[i][0] == key:
                self.data[i][1] = deleted
                break
        else:
            self.data.append([key, deleted])