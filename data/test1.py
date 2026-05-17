import random
import time
import tracemalloc

def measure_time(func, arr):
    start = time.perf_counter()
    func(arr)
    end = time.perf_counter()
    return end - start

def measure_time2(func, arr, arg):
    start = time.perf_counter()
    func(arr, arg)
    end = time.perf_counter()
    return end - start

def measure_time3(func, arr, arg1, arg2):
    start = time.perf_counter()
    func(arr, arg1, arg2)
    end = time.perf_counter()
    return end - start

def measure_ram(func, arr, arg1, arg2):
    tracemalloc.start()
    func(arr, arg1, arg2)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / 1024

def generate_array(n):
    arr = []
    for i in range(n):
        arr.append(random.randint(0, 10000))
    return arr

arr_ex = generate_array(3000)
s = random.randint(0, 10000)

#Задание 1
def search_element(n, arr):
    for i in range(len(arr)):
        if arr[i] == n:
            return True
    return False

#Задание 2
def secondmax(arr):
    max1 = 0
    max2 = 0
    for i in range(len(arr)):
        if i == 0:
            max1 = arr[i]
            max2 = arr[i]
        else:
            if arr[i] > max1:
                max2 = max1
                max1 = arr[i]
            elif arr[i] > max2:
                max2 = arr[i]
    return max2

#Задание 3
def binary_search(n, arr):
    arr = sorted(arr)
    low = 0
    high = len(arr) - 1
    mid = int
    while n in arr:
        mid = (low + high) // 2
        if arr[mid] < n:
            low = mid
        elif arr[mid] > n:
            high = mid
        else:
            return True
    return False


#Задание 4
def table_umnozhenie(n):
    table = []
    for i in range(n):
        row = []
        for j in range(n):
            row.append((i+1)*(j+1))
        table.append(row)
    return table

#Сортировка (quicksort)

def partition(arr, low, high):
    pivot = arr[high]
    i = low - 1
    for j in range(low, high):
        if arr[j] < pivot:
            i += 1
            temp = arr[i]
            arr[i] = arr[j]
            arr[j] = temp
    temp = arr[i+1]
    arr[i+1] = arr[high]
    arr[high] = temp
    return i+1

def quicksort(arr, low, high):
    if (low < high):
        pi = partition(arr, low, high)
        quicksort(arr, low, pi-1)
        quicksort(arr, pi+1, high)


if __name__ == '__main__':
    sizes = [100, 500, 750, 1000]
    for n in sizes:
        arr = generate_array(n)
        t = measure_time3(quicksort, arr, 0, n-1)
        ram = measure_ram(quicksort, arr, 0, n-1)
        print(n, t, ram)
