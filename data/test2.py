import math

AVERAGE_SPEED = 1.5


class Coord:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
    def distance_to(self, other: 'Coord') -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


class Ostanovka:
    def __init__(self, name = "", coords: Coord = Coord(), time_to_next: int = 0):
        self.name = name
        self.coords = coords
        self.time_to_next = time_to_next

class DoublyNode:
    def __init__(self, ostanovka = None, next_stop = None, prev_stop = None):
        self.ostanovka = ostanovka
        self.prev = prev_stop
        self.next = next_stop

class DoublyLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0
    def _calculate_time(self, coord1: Coord, coord2: Coord) -> int:
        distance = coord1.distance_to(coord2)
        return round(distance / AVERAGE_SPEED)

    def add_ostanovka(self, ostanovka: Ostanovka):
        new_node = DoublyNode(ostanovka)

        if self.size == 0:
            ostanovka.time_to_next = 0
            self.head = self.tail = new_node
            self.size += 1
            return

        
        if self.size == 1:
            time = self._calculate_time(self.head.ostanovka.coords, ostanovka.coords)
            self.head.ostanovka.time_to_next = time
            ostanovka.time_to_next = 0

            self.head.next = new_node
            new_node.prev = self.head
            self.tail = new_node
            self.size += 1
            return

        
        curr = self.head
        min_dist = float('inf')
        nearest_node = None

        while curr:
            dist = ostanovka.coords.distance_to(curr.ostanovka.coords)
            if dist < min_dist:
                min_dist = dist
                nearest_node = curr
            curr = curr.next

        
        if nearest_node == self.head:
            time = self._calculate_time(ostanovka.coords, self.head.ostanovka.coords)
            ostanovka.time_to_next = time

            new_node.next = self.head
            self.head.prev = new_node
            self.head = new_node
            self.size += 1
            return

        
        if nearest_node == self.tail:
            time = self._calculate_time(self.tail.ostanovka.coords, ostanovka.coords)
            self.tail.ostanovka.time_to_next = time
            ostanovka.time_to_next = 0

            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node
            self.size += 1
            return

        dist_to_prev = ostanovka.coords.distance_to(nearest_node.prev.ostanovka.coords)
        dist_to_next = ostanovka.coords.distance_to(nearest_node.next.ostanovka.coords)

        if dist_to_prev < dist_to_next:
            
            time1 = self._calculate_time(nearest_node.prev.ostanovka.coords, ostanovka.coords)
            time2 = self._calculate_time(ostanovka.coords, nearest_node.ostanovka.coords)

            nearest_node.prev.ostanovka.time_to_next = time1
            ostanovka.time_to_next = time2

            new_node.prev = nearest_node.prev
            new_node.next = nearest_node
            nearest_node.prev.next = new_node
            nearest_node.prev = new_node
        else:
            
            time1 = self._calculate_time(nearest_node.ostanovka.coords, ostanovka.coords)
            time2 = self._calculate_time(ostanovka.coords, nearest_node.next.ostanovka.coords)

            nearest_node.ostanovka.time_to_next = time1
            ostanovka.time_to_next = time2

            new_node.prev = nearest_node
            new_node.next = nearest_node.next
            nearest_node.next.prev = new_node
            nearest_node.next = new_node

        self.size += 1

    def display_forward(self):
        if not self.head:
            print("Маршрут пуст")
            return

        print("Маршрут:")
        curr = self.head
        i = 1
        total = 0
        while curr:
            ost = curr.ostanovka
            print(f"  {i}. {ost.name} ({ost.coords.x}, {ost.coords.y})", end="")
            if curr.next:
                print(f" —[{ost.time_to_next}мин]→")
                total += ost.time_to_next
            else:
                print(f" (конечная)")
            curr = curr.next
            i += 1
        print(f"  Общее время: {total} мин")

    def where_through_N(self, N, name):
        curr = self.head
        i = 0
        while curr.ostanovka.name != name:
            curr = curr.next
            if not curr:
                print(f"Остановка не найдена")
                return
        while i != N + 1:
            curr = curr.next
            if not curr:
                print(f"Остановка не найдена")
                return
            i = i + 1
        ost = curr.ostanovka
        print(f"  {ost.name} ({ost.coords.x}, {ost.coords.y})\n")
    
    def where_through_time(self, time, name):
        curr = self.head
        i = 0
        while curr.ostanovka.name != name:
            curr = curr.next
            if not curr:
                print(f"Остановка не найдена")
                return
        
        while curr != None:
            time -= curr.ostanovka.time_to_next
            if time >= 0:
                curr = curr.next
                ost = curr.ostanovka
                print(f"  {ost.name} ({ost.coords.x}, {ost.coords.y})", end="")
            else:
                print("\n")
                break

    def reverseList(self):
        if self.size < 2:
            return
        prev_time = 0
        curr = self.head   
        while curr:
            curr_time = curr.ostanovka.time_to_next
            temp = curr.next
            curr.next = curr.prev
            curr.prev = temp
            curr.ostanovka.time_to_next = prev_time
            prev_time = curr_time
        
            curr = temp
        
        old_head = self.head
        self.head = self.tail
        self.tail = old_head

    def generate_report(self, filename="route_report.txt"):
    
        if self.size == 0:
            print("Маршрут пуст, отчет не сформирован")
            return
    
        with open(filename, 'w', encoding='utf-8') as f:
        
            f.write("=" * 60 + "\n")
            f.write("           ПОДРОБНЫЙ ОТЧЕТ О МАРШРУТЕ\n")
            f.write("=" * 60 + "\n\n")
        
        
            f.write(f"Общее количество остановок: {self.size}\n")
        
            total_time = 0
            total_distance = 0.0
        
            curr = self.head
            while curr:
                total_time += curr.ostanovka.time_to_next
                if curr.next:
                    dist = curr.ostanovka.coords.distance_to(curr.next.ostanovka.coords)
                    total_distance += dist
                curr = curr.next
        
            f.write(f"Общее время в пути: {total_time} мин\n")
            f.write(f"Общее расстояние: {round(total_distance, 1)} усл. ед.\n")
            f.write("\n" + "-" * 60 + "\n\n")
        
        
            f.write("ОСТАНОВКИ:\n\n")
            f.write(f"{'№':<4} {'Название':<20} {'Координаты':<15} {'Время до след.':<15} {'Расстояние':<12}\n")
            f.write("-" * 60 + "\n")
        
            curr = self.head
            i = 1
            while curr:
                ost = curr.ostanovka
                coords_str = f"({ost.coords.x}, {ost.coords.y})"
                time_str = f"{ost.time_to_next} мин" if curr.next else "конечная"
            
                if curr.next:
                    dist = ost.coords.distance_to(curr.next.ostanovka.coords)
                    dist_str = f"{round(dist, 1)} усл. ед."
                else:
                    dist_str = "—"
            
                f.write(f"{i:<4} {ost.name:<20} {coords_str:<15} {time_str:<15} {dist_str:<12}\n")
                curr = curr.next
                i += 1
        
            f.write("\n" + "=" * 60 + "\n")
    
        print(f"Отчет сохранен в файл: {filename}")

if __name__ == "__main__":
    route = DoublyLinkedList()

    route.add_ostanovka(Ostanovka("Вокзал", Coord(0, 0)))
    route.add_ostanovka(Ostanovka("Центр", Coord(10, 0)))
    route.add_ostanovka(Ostanovka("Парк", Coord(20, 0)))
    route.add_ostanovka(Ostanovka("Школа", Coord(30, 0)))

    route.display_forward()

    route.add_ostanovka(Ostanovka("Библиотека", Coord(12, 3)))
    
    route.add_ostanovka(Ostanovka("Рынок", Coord(3, 2)))

    route.add_ostanovka(Ostanovka("Больница", Coord(40, 0)))

    route.add_ostanovka(Ostanovka("Памятник", Coord(30, 5)))

    route.add_ostanovka(Ostanovka("Депо", Coord(0, -5)))
    route.display_forward()

    route.where_through_N(3, "Вокзал")
    route.where_through_time(20, "Вокзал")

    route.reverseList()
    route.display_forward()

    route.generate_report()
