from rest_framework import viewsets, mixins, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.conf import settings
import stripe

from ..models import Cart, CartItem, Product
from ..serializers import CartSerializer, CartItemSerializer

def get_active_cart(user):
    cart, created = Cart.objects.get_or_create(user=user, status="Active")
    return cart

class CartViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).order_by("status", "-created_at")

    @action(detail=False, methods=["get"], url_path="my_cart")
    def retrieve_active_cart(self, request):
        cart = get_active_cart(request.user)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], serializer_class=CartItemSerializer, url_path="add_item")
    def add_item(self, request):
        user = request.user
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity")

        try:
            quantity = int(quantity) if quantity is not None else 1
            if quantity < 1: return Response({"error": "Quantity must be at least 1."}, status=400)
        except ValueError:
            return Response({"error": "Quantity must be an integer."}, status=400)

        if not product_id: return Response({"error": "Product ID is required."}, status=400)

        with transaction.atomic():
            cart = get_active_cart(user)
            if cart.status != "Active": return Response({"error": "Cart is closed."}, status=403)

            product = get_object_or_404(Product, pk=product_id)
            if product.in_stock < quantity:
                return Response({"error": f"Insufficient stock. Only {product.in_stock} left."}, status=400)

            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={"quantity": 0})
            
            cart_item.quantity += quantity
            cart_item.save()
            
            product.in_stock -= quantity
            product.save()

            cart.refresh_from_db()
            serializer = CartSerializer(cart)
            return Response(serializer.data, status=200 if not created else 201)

    @action(detail=False, methods=["post"], url_path="remove_item")
    def remove_item(self, request):
        product_id = request.data.get("product_id")
        quantity_to_remove = request.data.get("quantity")

        if not product_id: return Response({"error": "Product ID required"}, status=400)

        with transaction.atomic():
            cart = get_active_cart(request.user)
            if cart.status != "Active": return Response({"error": "Cart closed"}, status=403)

            try:
                cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
            except CartItem.DoesNotExist:
                return Response({"error": "Item not found"}, status=404)

            if quantity_to_remove:
                try:
                    qty = int(quantity_to_remove)
                    if qty < 1: raise ValueError
                except ValueError:
                    return Response({"error": "Invalid quantity"}, status=400)

                if qty >= cart_item.quantity:
                    self._delete_item(cart_item)
                    msg = "Item removed completely."
                else:
                    cart_item.quantity -= qty
                    cart_item.save()
                    cart_item.product.in_stock += qty
                    cart_item.product.save()
                    msg = "Quantity updated."
            else:
                self._delete_item(cart_item)
                msg = "Item removed completely."

            cart.refresh_from_db()
            serializer = CartSerializer(cart)
            return Response({"message": msg, "cart": serializer.data})

    def _delete_item(self, cart_item):
        cart_item.product.in_stock += cart_item.quantity
        cart_item.product.save()
        cart_item.delete()

    # --- Stripe Logic ---
    @action(detail=False, methods=["post"], url_path="checkout")
    def checkout(self, request):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        cart = get_active_cart(request.user)

        if cart.status != "Active": return Response({"error": "Cart closed"}, status=400)
        if not cart.items.exists(): return Response({"error": "Empty cart"}, status=400)

        amount_cents = int(cart.total_price[0] * 100)
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="usd",
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            )
            return Response({
                "clientSecret": intent["client_secret"],
                "publishableKey": settings.STRIPE_PUBLISHABLE_KEY,
                "amount": cart.total_price[0],
            })
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    @action(detail=False, methods=["post"], url_path="confirm_payment")
    def confirm_payment(self, request):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        payment_intent_id = request.data.get("payment_intent_id")
        if not payment_intent_id: return Response({"error": "Missing ID"}, status=400)

        cart = get_active_cart(request.user)
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if intent["status"] == "succeeded":
                if cart.status != "Paid":
                    cart.status = "Paid"
                    cart.save()
                serializer = CartSerializer(cart)
                return Response({"message": "Paid!", "order": serializer.data})
            return Response({"error": "Payment failed"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    @action(detail=False, methods=["post"])
    def clear_active_cart(self, request):
        cart = get_active_cart(request.user)
        if cart.status != "Active": return Response({"error": "Cart closed"}, status=403)
        with transaction.atomic():
            for item in cart.items.all():
                item.product.in_stock += item.quantity
                item.product.save()
            cart.delete()
        return Response(status=204)

class CartItemViewSet(
    mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        active_cart = get_active_cart(self.request.user)
        return CartItem.objects.filter(cart=active_cart)

    def perform_update(self, serializer):
        cart_item = self.get_object()
        with transaction.atomic():
            if cart_item.cart.status != "Active": raise PermissionDenied("Cart closed")
            
            new_qty = serializer.validated_data.get("quantity")
            old_qty = cart_item.quantity
            if new_qty is None: return serializer.save()

            diff = new_qty - old_qty
            if diff > 0:
                if cart_item.product.in_stock < diff:
                    raise PermissionDenied("Insufficient stock")
                cart_item.product.in_stock -= diff
            elif diff < 0:
                cart_item.product.in_stock += abs(diff)
            
            cart_item.product.save()
            serializer.save()

    def perform_destroy(self, instance):
        with transaction.atomic():
            if instance.cart.status != "Active": raise PermissionDenied("Cart closed")
            instance.product.in_stock += instance.quantity
            instance.product.save()
            instance.delete()