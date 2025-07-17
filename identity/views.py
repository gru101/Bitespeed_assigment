from django.views import View 
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Q
from .models import Contacts
import json

@method_decorator(csrf_exempt, name="dispatch")
class Identify(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"message": "invalid json"}, status=400)
        
        email = data.get("email")
        phone = data.get("phoneNumber")

        if not email and not phone:
            return JsonResponse({"message": "email or phoneNumber required"}, status=400)

        # Get matching contacts
        email_qs = Contacts.objects.filter(email=email)
        phone_qs = Contacts.objects.filter(phoneNumber=phone)

        # Collect all related contacts (using linkedId or self id)
        related_contacts = set()

        for qs in [email_qs, phone_qs]:
            if qs.exists():
                primary_id = qs[0].linkedId if qs[0].linkedId else qs[0].id
                group = Contacts.objects.filter(Q(id=primary_id) | Q(linkedId=primary_id))
                related_contacts.update(group)

        related_contacts = list(related_contacts)

        # CASE 1: Neither email nor phone exists
        if not email_qs.exists() and not phone_qs.exists():
            new = Contacts.objects.create(email=email, phoneNumber=phone, linkPrecedence="PM")
            return JsonResponse({"contact": {
                "primaryContatctId": new.id,
                "emails": [new.email] if new.email else [],
                "phoneNumbers": [new.phoneNumber] if new.phoneNumber else [],
                "secondaryContactIds": []
            }})

        # CASE 2: Only email exists
        if email_qs.exists() and not phone_qs.exists() and phone:
            # Add phone as secondary
            primary = email_qs[0].linkedId or email_qs[0].id
            Contacts.objects.create(email=None, phoneNumber=phone, linkedId=primary, linkPrecedence="SC")
            related_contacts = Contacts.objects.filter(Q(id=primary) | Q(linkedId=primary))

        # CASE 3: Only phone exists
        if phone_qs.exists() and not email_qs.exists() and email:
            primary = phone_qs[0].linkedId or phone_qs[0].id
            Contacts.objects.create(email=email, phoneNumber=None, linkedId=primary, linkPrecedence="SC")
            related_contacts = Contacts.objects.filter(Q(id=primary) | Q(linkedId=primary))

        # CASE 4: Both exist but in different groups → merge
        if email_qs.exists() and phone_qs.exists():
            email_primary = email_qs[0].linkedId or email_qs[0].id
            phone_primary = phone_qs[0].linkedId or phone_qs[0].id

            if email_primary != phone_primary:
                # choose oldest as primary
                email_primary_obj = Contacts.objects.get(id=email_primary)
                phone_primary_obj = Contacts.objects.get(id=phone_primary)
                oldest = email_primary_obj if email_primary_obj.createdAt <= phone_primary_obj.createdAt else phone_primary_obj
                to_secondary = phone_primary_obj if oldest.id == email_primary_obj.id else email_primary_obj

                # update
                to_secondary.linkPrecedence = "SC"
                to_secondary.linkedId = oldest.id
                to_secondary.save()

                # update all contacts in secondary group
                Contacts.objects.filter(linkedId=to_secondary.id).update(linkedId=oldest.id)

                related_contacts = Contacts.objects.filter(Q(id=oldest.id) | Q(linkedId=oldest.id))

        # CASE 5: already in same group → do nothing
        if not related_contacts:
            # fallback: get from email or phone
            primary = email_qs[0].linkedId or email_qs[0].id if email_qs.exists() else phone_qs[0].linkedId or phone_qs[0].id
            related_contacts = Contacts.objects.filter(Q(id=primary) | Q(linkedId=primary))

        # Build response
        primaries = [c for c in related_contacts if c.linkPrecedence == "PM" or c.id == (c.linkedId or c.id)]
        primary = sorted(primaries, key=lambda c: c.createdAt)[0]  # oldest PM as true primary

        emails = sorted({c.email for c in related_contacts if c.email})
        phones = sorted({c.phoneNumber for c in related_contacts if c.phoneNumber})
        secondaries = [c.id for c in related_contacts if c.id != primary.id]

        return JsonResponse({"contact": {
            "primaryContatctId": primary.id,
            "emails": emails,
            "phoneNumbers": phones,
            "secondaryContactIds": secondaries
        }})
