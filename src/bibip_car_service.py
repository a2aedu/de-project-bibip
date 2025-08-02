from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale
from decimal import Decimal
from datetime import datetime
from collections import defaultdict
import os


class CarService:
    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = root_directory_path
        self.LINE_LENGTH = 501

        # Основные файлы
        self.CARS_FILE = os.path.join(root_directory_path, "cars.txt")
        self.CARS_INDEX_FILE = os.path.join(root_directory_path, "cars_index.txt")
        self.MODELS_FILE = os.path.join(root_directory_path, "models.txt")
        self.MODELS_INDEX_FILE = os.path.join(root_directory_path, "models_index.txt")
        self.SALES_FILE = os.path.join(root_directory_path, "sales.txt")
        self.SALES_INDEX_FILE = os.path.join(root_directory_path, "sales_index.txt")

        # Создаем файлы, если они не существуют
        for file in [self.CARS_FILE, self.MODELS_FILE, self.SALES_FILE]:
            os.makedirs(os.path.dirname(file), exist_ok=True)
            if not os.path.exists(file):
                open(file, 'w').close()

    def _pad_line(self, data: str) -> str:
        return data.ljust(self.LINE_LENGTH - 1) + "\n"

    def _read_index(self, file_path: str) -> list:
        if not os.path.exists(file_path):
            return []
        with open(file_path, "r") as f:
            return [tuple(line.strip().split(";")) for line in f]

    def _write_index(self, file_path: str, index_list: list):
        with open(file_path, "w") as f:
            for i, (key, pos) in enumerate(index_list):
                f.write(f"{key};{pos}\n")

    def _insert_sorted_index(self, index_list: list, new_key: str) -> list:
        index_list.append((new_key, len(index_list)))
        index_list.sort(key=lambda x: x[0])
        return index_list

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:
        model_data = f"{model.id};{model.name};{model.brand}"
        padded_line = self._pad_line(model_data)

        with open(self.MODELS_FILE, "a") as f:
            f.write(padded_line)

        index = self._read_index(self.MODELS_INDEX_FILE)
        index = self._insert_sorted_index(index, str(model.id))
        self._write_index(self.MODELS_INDEX_FILE, index)

        return model

    # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Car:
        car_data = f"{car.vin};{car.model};{car.price};{car.date_start.isoformat()};{car.status.value}"
        padded_line = self._pad_line(car_data)

        with open(self.CARS_FILE, "a") as f:
            f.write(padded_line)

        index = self._read_index(self.CARS_INDEX_FILE)
        index = self._insert_sorted_index(index, car.vin)
        self._write_index(self.CARS_INDEX_FILE, index)

        return car

    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        # Записываем продажу
        sale_data = f"{sale.sales_number};{sale.car_vin};{sale.cost};{sale.sales_date.isoformat()}"
        padded_sale = self._pad_line(sale_data)

        with open(self.SALES_FILE, "a") as f:
            f.write(padded_sale)

        # Обновляем индекс продаж
        index = self._read_index(self.SALES_INDEX_FILE)
        index = self._insert_sorted_index(index, sale.sales_number)
        self._write_index(self.SALES_INDEX_FILE, index)

        # Обновляем статус автомобиля
        cars_index = self._read_index(self.CARS_INDEX_FILE)
        vin_to_line = dict(cars_index)

        if sale.car_vin not in vin_to_line:
            raise ValueError(f"VIN {sale.car_vin} не найден в индексе.")

        line_number = int(vin_to_line[sale.car_vin])
        line_pos = line_number * self.LINE_LENGTH

        # Читаем и обновляем файл cars.txt
        with open(self.CARS_FILE, "r+") as f:
            # Читаем всю строку
            f.seek(line_pos)
            line = f.read(self.LINE_LENGTH)

            if len(line) < self.LINE_LENGTH:
                line = line.ljust(self.LINE_LENGTH)

            content = line[:self.LINE_LENGTH-1].rstrip()  
            parts = content.split(";")

            if len(parts) != 5:
                raise ValueError(f"Ошибка разбора строки VIN {sale.car_vin}: {content}")

            # Обновляем статус
            parts[4] = "sold"
            updated_content = ";".join(parts)
            updated_line = self._pad_line(updated_content)

            # Записываем обратно
            f.seek(line_pos)
            f.write(updated_line)
            f.flush()  # Гарантируем запись

        return Car(
            vin=parts[0],
            model=int(parts[1]),
            price=Decimal(parts[2]),
            date_start=datetime.fromisoformat(parts[3]),
            status=CarStatus(parts[4])
        )

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        cars = []
        with open(self.CARS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(";")
                if len(parts) != 5:
                    continue
                vin, model_id, price, date_start, car_status = parts
                if car_status == status.value:
                    cars.append(Car(
                        vin=vin,
                        model=int(model_id),
                        price=Decimal(price),
                        date_start=datetime.fromisoformat(date_start),
                        status=CarStatus(car_status)
                    ))

        return cars

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        # Читаем индекс cars
        cars_index = self._read_index(self.CARS_INDEX_FILE)
        vin_to_line = dict(cars_index)

        if vin not in vin_to_line:
            return None

        line_number = int(vin_to_line[vin])

        # Читаем строку из cars
        with open(self.CARS_FILE, "r") as f:
            f.seek(line_number * self.LINE_LENGTH)
            line = f.read(self.LINE_LENGTH).strip()
            parts = line.split(";")
            if len(parts) != 5:
                return None
            vin, model_id, price, date_start, status = parts

        # Читаем модель
        models_index = self._read_index(self.MODELS_INDEX_FILE)
        model_id_to_line = dict(models_index)

        if model_id not in model_id_to_line:
            return None

        model_line_number = int(model_id_to_line[model_id])

        with open(self.MODELS_FILE, "r") as f:
            f.seek(model_line_number * self.LINE_LENGTH)
            model_line = f.read(self.LINE_LENGTH).strip()
            model_parts = model_line.split(";")
            if len(model_parts) != 3:
                return None
            _, model_name, model_brand = model_parts

        # Ищем продажу (проверяем существование файла)
        sales_date = None
        sales_cost = None

        if os.path.exists(self.SALES_FILE):
            with open(self.SALES_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(";")
                    if len(parts) >= 3 and parts[1] == vin:
                        sales_date = datetime.fromisoformat(parts[3])
                        sales_cost = Decimal(parts[2])
                        break

        return CarFullInfo(
            vin=vin,
            car_model_name=model_name,
            car_model_brand=model_brand,
            price=Decimal(price),
            date_start=datetime.fromisoformat(date_start),
            status=CarStatus(status),
            sales_date=sales_date,
            sales_cost=sales_cost
        )

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        # Чтение индекса
        cars_index = self._read_index(self.CARS_INDEX_FILE)
        vin_to_line = dict(cars_index)

        if vin not in vin_to_line:
            raise ValueError(f"VIN {vin} не найден в индексе.")

        line_number = int(vin_to_line[vin])

        # Чтение и обновление строки
        with open(self.CARS_FILE, "r+") as f:
            f.seek(line_number * self.LINE_LENGTH)
            line = f.read(self.LINE_LENGTH).strip()
            parts = line.split(";")
            if len(parts) != 5:
                raise ValueError("Некорректный формат строки автомобиля")

            parts[0] = new_vin
            updated_line = self._pad_line(";".join(parts))
            f.seek(line_number * self.LINE_LENGTH)
            f.write(updated_line)

        # Обновляем индекс
        new_index = []
        for v, pos in cars_index:
            if v == vin:
                new_index.append((new_vin, pos))
            else:
                new_index.append((v, pos))

        new_index.sort(key=lambda x: x[0])
        self._write_index(self.CARS_INDEX_FILE, new_index)

        return Car(
            vin=new_vin,
            model=int(parts[1]),
            price=Decimal(parts[2]),
            date_start=datetime.fromisoformat(parts[3]),
            status=CarStatus(parts[4])
        )

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        # Находим VIN автомобиля по номеру продажи
        vin = None
        if os.path.exists(self.SALES_FILE):
            with open(self.SALES_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(";")
                    if len(parts) >= 1 and parts[0] == sales_number:
                        vin = parts[1]
                        break

        if not vin:
            raise ValueError(f"Продажа с номером {sales_number} не найдена")

        # Удаляем продажу из sales.txt
        if os.path.exists(self.SALES_FILE):
            with open(self.SALES_FILE, "r") as f:
                sales_lines = f.readlines()

            with open(self.SALES_FILE, "w") as f:
                for line in sales_lines:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(";")
                    if len(parts) >= 1 and parts[0] != sales_number:
                        f.write(line + "\n")

        # Обновляем статус автомобиля
        cars_index = self._read_index(self.CARS_INDEX_FILE)
        vin_to_line = dict(cars_index)

        if vin not in vin_to_line:
            raise ValueError(f"Автомобиль с VIN {vin} не найден")

        line_number = int(vin_to_line[vin])

        with open(self.CARS_FILE, "r+") as f:
            f.seek(line_number * self.LINE_LENGTH)
            line = f.read(self.LINE_LENGTH).strip()
            parts = line.split(";")
            if len(parts) != 5:
                raise ValueError("Некорректный формат строки автомобиля")

            parts[4] = "available"
            updated_line = self._pad_line(";".join(parts))
            f.seek(line_number * self.LINE_LENGTH)
            f.write(updated_line)

        return Car(
            vin=parts[0],
            model=int(parts[1]),
            price=Decimal(parts[2]),
            date_start=datetime.fromisoformat(parts[3]),
            status=CarStatus(parts[4])
        )

    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        # Собираем статистику продаж {model_id: sales_count}
        model_sales = defaultdict(int)

        # Сначала получаем соответствие VIN - model_id
        vin_to_model = {}
        if os.path.exists(self.CARS_FILE):
            with open(self.CARS_FILE, "r") as f:
                for line in f:
                    parts = line.strip().split(";")
                    if len(parts) >= 2:
                        vin_to_model[parts[0]] = parts[1]

        # Считаем количество продаж по model_id
        if os.path.exists(self.SALES_FILE):
            with open(self.SALES_FILE, "r") as f:
                for line in f:
                    parts = line.strip().split(";")
                    if len(parts) >= 2 and parts[1] in vin_to_model:
                        model_id = vin_to_model[parts[1]]
                        model_sales[model_id] += 1

        # Получаем цены моделей для сортировки
        model_prices = {}
        models_index = self._read_index(self.MODELS_INDEX_FILE)
        if os.path.exists(self.MODELS_FILE):
            with open(self.MODELS_FILE, "r") as f:
                for line_num, line in enumerate(f):
                    parts = line.strip().split(";")
                    if len(parts) >= 3:
                        model_id = parts[0]
                        # Предполагаем, что цена хранится в 4-м поле
                        price = Decimal(parts[3]) if len(parts) >= 4 else Decimal(0)
                        model_prices[model_id] = price

        # Сортируем модели по продажам и цене
        sorted_models = sorted(
            model_sales.items(),
            key=lambda item: (-item[1], -model_prices.get(item[0], Decimal(0))),
        )[:3]

        result = []
        for model_id, sales_count in sorted_models:
            # Получаем информацию о модели через индекс
            model_info = None
            models_index = self._read_index(self.MODELS_INDEX_FILE)
            for mid, line_num in models_index:
                if mid == model_id:
                    with open(self.MODELS_FILE, "r") as f:
                        for i, line in enumerate(f):
                            if i == int(line_num):
                                parts = line.strip().split(";")
                                if len(parts) >= 3:
                                    model_info = {
                                        'name': parts[1],
                                        'brand': parts[2]
                                    }
                                break
                    break

            if model_info:
                result.append(ModelSaleStats(
                    car_model_name=model_info['name'],
                    brand=model_info['brand'],
                    sales_number=sales_count
                ))

        return result
