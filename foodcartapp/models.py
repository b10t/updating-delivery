from collections import defaultdict

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Count, F, Prefetch, Sum
from geolocation.models import calculate_distance
from phonenumber_field.modelfields import PhoneNumberField


class OrderQuerySet(models.QuerySet):
    def cost(self):
        """Возвращает стоимость заказа."""
        return self.annotate(
            cost=Sum(
                F('elements__quantity') *
                F('elements__price')
            )
        )

    def manager_orders(self):
        """Возвращает заказы менеджера."""
        return self.exclude(status=Order.COMPLETED).order_by('status')

    def serving_restaurants(self):
        """Возвращает список ресторанов."""
        for order in self:
            if order.status != Order.UNPROCESSED and not order.serving_restaurant:
                order.serving_restaurants = []
                continue

            if order.serving_restaurant:
                order.serving_restaurant.distance = calculate_distance(
                    order.address,
                    order.serving_restaurant.address
                )
                order.serving_restaurants = [order.serving_restaurant]
                continue

            restaurant_ids = []
            product_in_restaurants = defaultdict(set)

            menu_items = (RestaurantMenuItem.objects
                          .filter(availability=True)
                          .values_list('product', 'restaurant'))

            for product, restaurant in menu_items:
                product_in_restaurants[product].add(restaurant)

            for element in order.elements.all():  # type: ignore
                restaurant_ids.append(
                    product_in_restaurants[element.product_id]
                )

            if not restaurant_ids:
                order.serving_restaurants = []
                continue

            restaurant_ids = set.intersection(*restaurant_ids)

            restaurants = list(
                Restaurant.objects.filter(pk__in=restaurant_ids))

            for restaurant in restaurants:
                restaurant.distance = calculate_distance(
                    order.address,
                    restaurant.address
                )

            order.serving_restaurants = sorted(
                restaurants, key=lambda restaurant: restaurant.distance
            )

        return self


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class Order(models.Model):
    """Заказы."""
    UNPROCESSED = 0
    GOING_TO = 1
    DELIVERED = 2
    COMPLETED = 9

    ORDER_STATUS = (
        (UNPROCESSED, 'Необработан'),
        (GOING_TO, 'Собирается'),
        (DELIVERED, 'Доставляется'),
        (COMPLETED, 'Завершён'),
    )

    PAYMENT = (
        ('E', 'Электронно'),
        ('C', 'Наличностью'),
    )

    address = models.CharField(
        verbose_name='Адрес доставки',
        max_length=200
    )
    firstname = models.CharField(
        verbose_name='Имя',
        max_length=50
    )
    lastname = models.CharField(
        verbose_name='Фамилия',
        max_length=50
    )
    phonenumber = PhoneNumberField(
        verbose_name='Телефон'
    )
    status = models.SmallIntegerField(
        verbose_name='Статус заказа',
        db_index=True,
        choices=ORDER_STATUS,
        default=UNPROCESSED
    )
    method_payment = models.CharField(
        verbose_name='Способ оплаты',
        db_index=True,
        choices=PAYMENT,
        max_length=1
    )
    comment = models.TextField(
        verbose_name='Комментарий',
        blank=True,
    )
    serving_restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='Обслуживающий ресторан',
        related_name='orders',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(
        verbose_name='Оформлен в',
        db_index=True,
        auto_now_add=True
    )
    called_at = models.DateTimeField(
        verbose_name='Позвонили в',
        blank=True,
        null=True
    )
    delivered_at = models.DateTimeField(
        verbose_name='Доставили в',
        blank=True,
        null=True
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'{self.lastname} {self.firstname} - {self.address}'


class OrderElement(models.Model):
    """Элементы заказа."""
    order = models.ForeignKey(
        Order,
        verbose_name='Заказ',
        related_name='elements',
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        verbose_name='Продукт',
        related_name='order_elements',
        on_delete=models.CASCADE,
    )
    quantity = models.IntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1), MaxValueValidator(25)]
    )
    price = models.DecimalField(
        verbose_name='Цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказов'

    def __str__(self):
        return f'{self.product} - {self.quantity} шт.'
