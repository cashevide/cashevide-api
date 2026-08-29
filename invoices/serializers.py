from pathlib import Path

from django.db import transaction
from rest_framework import serializers

from invoices.models import Invoice, InvoiceItem, PaymentRecord
from users.models import UserProfile, UserSubscription

template_dir = Path(__file__).resolve().parent / "templates" / "invoices"
ALLOWED_TEMPLATES = [
    item.stem for item in template_dir.iterdir() if item.suffix == ".html"
]


class InvoiceItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = InvoiceItem
        fields = [
            "id",
            "invoice",
            "product",
            "title",
            "description",
            "quantity",
            "unit_type",
            "unit_price",
            "total",
            "created_at",
            "updated_at",
        ]

        read_only_fields = ["created_at", "updated_at", "total"]

        extra_kwargs = {"invoice": {"required": False}}


class PaymentRecordSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = PaymentRecord
        fields = [
            "id",
            "invoice",
            "amount",
            "payment_date",
            "payment_method",
            "note",
            "created_at",
            "updated_at",
        ]

        read_only_fields = ["created_at", "updated_at"]

        extra_kwargs = {"invoice": {"required": False}}


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)
    payments = PaymentRecordSerializer(many=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "user",
            "client",
            "name",
            "email",
            "phone",
            "address",
            "business_snapshot",
            "invoice_number",
            "items",
            "status",
            "currency",
            "issue_date",
            "due_date",
            "subtotal",
            "discount",
            "total_amount",
            "amount_paid",
            "balance_due",
            "payments",
            "template",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = [
            "id",
            "user",
            "business_snapshot",
            "invoice_number",
            "status",
            "subtotal",
            "total_amount",
            "amount_paid",
            "balance_due",
            "created_at",
            "updated_at",
        ]

    def validate_template(self, value):

        if value not in ALLOWED_TEMPLATES:
            raise serializers.ValidationError(
                f"'{value}' is not a valid template. Choose from:"
                f" {', '.join(ALLOWED_TEMPLATES)}."
            )

        if self.instance and self.instance.template != value:
            raise serializers.ValidationError(
                "Template cannot be changed once the invoice is created."
            )

        return value

    @transaction.atomic
    def create(self, validated_data):
        user = self.context.get("request").user  # type:ignore

        if (
            user.tier == UserSubscription.Tier.COMMUNITY
            and validated_data.get("template") != "classic"
        ):
            user_profile = UserProfile.objects.select_for_update().get(user=user)

            if user_profile.credit_points <= 0:
                raise serializers.ValidationError(
                    "You do not have enough credit points to create a new invoice."
                )

        items_data = validated_data.pop("items", [])
        payments_data = validated_data.pop("payments", [])

        invoice = Invoice.objects.create(**validated_data)

        for item in items_data:
            item.pop("id", None)
            InvoiceItem.objects.create(invoice=invoice, **item)

        for payment in payments_data:
            payment.pop("id", None)
            PaymentRecord.objects.create(invoice=invoice, **payment)

        return invoice

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        payments_data = validated_data.pop("payments", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        instance.update_financials()

        if items_data is not None:
            item_pool = {item.id: item for item in instance.items.all()}
            keep_item_ids = []

            for item_dic in items_data:
                item_id = item_dic.get("id", None)

                if item_id and item_id in item_pool:
                    item_instance = item_pool[item_id]

                    for attr, value in item_dic.items():
                        if attr != "id":
                            setattr(item_instance, attr, value)

                    item_instance.save()
                    instance.update_financials()

                    keep_item_ids.append(item_instance.id)
                else:
                    item_dic.pop("id", None)

                    new_item = InvoiceItem.objects.create(invoice=instance, **item_dic)
                    keep_item_ids.append(new_item.id)  # type:ignore

            for old_id, old_item in item_pool.items():
                if old_id not in keep_item_ids:
                    old_item.delete()
                    instance.update_financials()

        if payments_data is not None:
            payment_pool = {payment.id: payment for payment in instance.payments.all()}
            keep_payment_ids = []

            for payment_dic in payments_data:
                payment_id = payment_dic.get("id", None)

                if payment_id and payment_id in payment_pool:
                    payment_instance = payment_pool[payment_id]

                    for attr, value in payment_dic.items():
                        if attr != "id":
                            setattr(payment_instance, attr, value)

                    payment_instance.save()
                    instance.update_financials()

                    keep_payment_ids.append(payment_instance.id)
                else:
                    payment_dic.pop("id", None)

                    new_payment_record = PaymentRecord.objects.create(
                        invoice=instance, **payment_dic
                    )
                    keep_payment_ids.append(new_payment_record.id)  # type:ignore

            for old_id, old_payment in payment_pool.items():
                if old_id not in keep_payment_ids:
                    old_payment.delete()
                    instance.update_financials()

        return instance
