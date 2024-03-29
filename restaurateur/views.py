from django import forms
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from foodcartapp.models import Order, Product, Restaurant
from geolocation.geocode_api import calculate_distance


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    default_availability = {restaurant.id: False for restaurant in restaurants}
    products_with_restaurants = []
    for product in products:

        availability = {
            **default_availability,
            **{item.restaurant_id: item.availability for item in product.menu_items.all()},
        }
        orderer_availability = [availability[restaurant.id]
                                for restaurant in restaurants]

        products_with_restaurants.append(
            (product, orderer_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurants': products_with_restaurants,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = (
        Order.objects
        .get_manager_orders()  # type: ignore
        .get_cost()
        .get_serving_restaurants()
    )

    order_items = []

    for order in orders:
        url = reverse_lazy('admin:foodcartapp_order_change', args=(order.id,))

        restaurants = order.serving_restaurants

        for restaurant in restaurants:
            restaurant.distance = calculate_distance(
                order.address,
                restaurant.address
            )

        order.serving_restaurants = sorted(
            restaurants, key=lambda restaurant: restaurant.distance
        )

        order_item = {
            'id': order.id,
            'status': order.get_status_display(),
            'method_payment': order.get_method_payment_display(),
            'cost': order.cost,
            'client': f'{order.firstname} {order.lastname}',
            'phonenumber': order.phonenumber,
            'address': order.address,
            'comment': order.comment,
            'order_status': order.status,
            'serving_restaurants': order.serving_restaurants,
            'url': url,
        }
        order_items.append(order_item)

    return render(
        request,
        template_name='order_items.html',
        context={
            'order_items': order_items,
            'Order': Order
        }
    )
