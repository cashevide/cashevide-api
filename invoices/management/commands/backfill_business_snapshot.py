from django.core.management.base import BaseCommand

from invoices.models import Invoice


class Command(BaseCommand):
    def handle(self, *args, **options):
        updated_count = 0
        skipped_count = 0

        queryset = Invoice.objects.filter(business_snapshot={})

        for invoice in queryset:
            if hasattr(invoice.user, "business_profile"):
                bp = invoice.user.business_profile

                snapshot_dict = {
                    "business_name": bp.business_name,
                    "logo": bp.logo.url if bp.logo else "",
                    "gst_number": bp.gst_number,
                    "vat_number": bp.vat_number,
                    "address": bp.address,
                    "phone_number": bp.phone_number,
                    "business_email": bp.business_email,
                    "website": bp.website,
                }

                Invoice.objects.filter(pk=invoice.pk).update(
                    business_snapshot=snapshot_dict
                )

                updated_count += 1

            else:
                skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Backfill complete. Updated: {updated_count}, Skipped: {skipped_count}"
            )
        )
