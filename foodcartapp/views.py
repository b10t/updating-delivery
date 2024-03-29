import json

from django.db import transaction
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ListField, ModelSerializer

from .models import Order, OrderElement, Product


class OrderElementSerializer(ModelSerializer):
    class Meta:
        model = OrderElement
        fields = [
            'product',
            'quantity',
        ]


class OrderSerializer(ModelSerializer):
    products = ListField(
        child=OrderElementSerializer(),
        write_only=True
    )

    class Meta:
        model = Order
        fields = [
            'address',
            'firstname',
            'lastname',
            'phonenumber',
            'products',
        ]


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    """Оформление заказа."""
    order_content = request.data

    serializer = OrderSerializer(data=order_content)
    serializer.is_valid(raise_exception=True)

    products = order_content.get('products')

    if not products:
        error_content = {
            'products': ['Этот список не может быть пустым.']}
        return Response(error_content, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        order = Order.objects.create(
            address=order_content.get('address'),
            firstname=order_content.get('firstname'),
            lastname=order_content.get('lastname'),
            phonenumber=order_content.get('phonenumber'),
        )

        order_elements = []

        for product_content in products:
            product = Product.objects.get(pk=product_content.get('product'))

            order_elements.append(
                OrderElement(
                    order=order,
                    product=product,
                    quantity=product_content.get('quantity'),
                    price=product.price,
                )
            )

        OrderElement.objects.bulk_create(order_elements)

    return Response(OrderSerializer(order).data)
