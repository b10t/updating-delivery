import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Order, OrderElement, Product


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
    error_content = {'error': ''}
    order_content = request.data

    order = Order(
        delivery_address=order_content.get('address'),
        first_name=order_content.get('firstname'),
        last_name=order_content.get('lastname'),
        phone_number=order_content.get('phonenumber'),
    )
    order.save()

    if 'products' not in order_content:
        error_content['error'] = 'products: Обязательное поле.'
        return Response(error_content, status=status.HTTP_400_BAD_REQUEST)

    products = order_content.get('products')

    if not isinstance(products, list):
        error_content['error'] = 'products: Ожидался list со значениями.'
        return Response(error_content, status=status.HTTP_400_BAD_REQUEST)
    else:
        if isinstance(products, list) and not products:
            error_content['error'] = 'products: Этот список не может быть пустым.'
            return Response(error_content, status=status.HTTP_400_BAD_REQUEST)

    for product_content in products:
        if 'product' not in product_content or 'quantity' not in product_content:
            error_content['error'] = 'Нет полей: product или quantity.'
            return Response(error_content, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(pk=product_content.get('product'))
        except Product.DoesNotExist:
            error_content['error'] = 'Такой продукт не найден.'
            return Response(error_content, status=status.HTTP_404_NOT_FOUND)

        OrderElement(
            order=order,
            product=product,
            quantity=product_content.get('quantity')
        ).save()

    return JsonResponse({})
