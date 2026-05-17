class Task:
    def __init__(self, id: int, description: str = "", priority: int = 1):
        self.id = id
        self.description = description
        self.priority = priority

class Queue:
    def __init__(self):
        self.items = []

    def enqueue(self, task: Task):
        self.items.append(task)

    def dequeue(self):
        if self.isEmpty():
            return None
        return self.items.pop(0)
    
    def front(self):
        if self.isEmpty():
            return None
        return self.items[0]

    def isEmpty(self):
        return len(self.items) == 0
    
    def printqueue(self):
        print("================= СПИСОК ЗАДАЧ =================")
        for i in range(len(self.items)):
            ost = self.items[i]
            print(f'{i+1}. {ost.description} (приоритет = {ost.priority}, id = {ost.id})')

if __name__ == "__main__":
    queue = Queue()
    task1 = Task(1, "Сделать кофе", 1)
    queue.enqueue(task1)
    task2 = Task(2, "Сделать отчет", 3)
    queue.enqueue(task2)
    queue.printqueue()

    print(queue.front().description)

    queue.dequeue()
    print(queue.front().description)