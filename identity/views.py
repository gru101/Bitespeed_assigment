from django.views import View 
from .models import Contacts
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Q
# Create your views here.
from django.http import JsonResponse

@method_decorator(csrf_exempt, name="dispatch")
class Identify(View):
    @classmethod
    def get_oldest(cls, email_query, phonenumber_query):
        email_created = email_query[0].createdAt
        phone_created = phonenumber_query[0].createdAt
        if email_created < phone_created:
            return {"oldest": "email"}
        else:
            return {"oldest": "phonenumber"}

    def post(self, request, *args, **kwargs):
        try: 
            data = json.loads(request.body)
        except:
            return JsonResponse(data={"message":"invalid json"}, status=400)

        email = data.get("email")
        phonenumber = data.get("phoneNumber")
        email_query = Contacts.objects.filter(email=email).order_by("createdAt")
        phonenumber_query = Contacts.objects.filter(phoneNumber=phonenumber).order_by("createdAt")

        # Both email & phone given
        if email and phonenumber:
            if email_query.exists() and phonenumber_query.exists():
                oldest = self.get_oldest(email_query, phonenumber_query)
                if oldest["oldest"] == "email":
                    newer = phonenumber_query[0]
                    primary = email_query[0]
                else:
                    newer = email_query[0]
                    primary = phonenumber_query[0]
                # merge: make newer secondary
                newer.linkedId = primary.id
                newer.linkPrecedence = "secondary"
                newer.save()
                contacts = Contacts.objects.filter(Q(id=primary.id) | Q(linkedId=primary.id))
                return JsonResponse({"contact": {
                    "primaryContactId": primary.id,
                    "emails": [c.email for c in contacts],
                    "phoneNumbers": [c.phoneNumber for c in contacts],
                    "secondaryContactIds": [c.id for c in contacts if c.id != primary.id]
                }})
            elif email_query.exists():
                # phone is new
                new = Contacts.objects.create(phoneNumber=phonenumber, linkedId=email_query[0].id, linkPrecedence="secondary")
                contacts = Contacts.objects.filter(Q(id=email_query[0].id) | Q(linkedId=email_query[0].id))
                return JsonResponse({"contact": {
                    "primaryContactId": email_query[0].id,
                    "emails": [c.email for c in contacts],
                    "phoneNumbers": [c.phoneNumber for c in contacts],
                    "secondaryContactIds": [c.id for c in contacts if c.id != email_query[0].id]
                }})
            elif phonenumber_query.exists():
                # email is new
                new = Contacts.objects.create(email=email, linkedId=phonenumber_query[0].id, linkPrecedence="secondary")
                contacts = Contacts.objects.filter(Q(id=phonenumber_query[0].id) | Q(linkedId=phonenumber_query[0].id))
                return JsonResponse({"contact": {
                    "primaryContactId": phonenumber_query[0].id,
                    "emails": [c.email for c in contacts],
                    "phoneNumbers": [c.phoneNumber for c in contacts],
                    "secondaryContactIds": [c.id for c in contacts if c.id != phonenumber_query[0].id]
                }})
            else:
                # both are new
                new = Contacts.objects.create(email=email, phoneNumber=phonenumber, linkPrecedence="primary")
                return JsonResponse({"contact": {
                    "primaryContactId": new.id,
                    "emails": [new.email],
                    "phoneNumbers": [new.phoneNumber],
                    "secondaryContactIds": []
                }})

        # only email
        elif email:
            if email_query.exists():
                contacts = Contacts.objects.filter(Q(id=email_query[0].id) | Q(linkedId=email_query[0].id))
                return JsonResponse({"contact": {
                    "primaryContactId": email_query[0].id,
                    "emails": [c.email for c in contacts],
                    "phoneNumbers": [c.phoneNumber for c in contacts],
                    "secondaryContactIds": [c.id for c in contacts if c.id != email_query[0].id]
                }})
            else:
                new = Contacts.objects.create(email=email, linkPrecedence="primary")
                return JsonResponse({"contact": {
                    "primaryContactId": new.id,
                    "emails": [new.email],
                    "phoneNumbers": [],
                    "secondaryContactIds": []
                }})

        # only phone
        elif phonenumber:
            if phonenumber_query.exists():
                contacts = Contacts.objects.filter(Q(id=phonenumber_query[0].id) | Q(linkedId=phonenumber_query[0].id))
                return JsonResponse({"contact": {
                    "primaryContactId": phonenumber_query[0].id,
                    "emails": [c.email for c in contacts],
                    "phoneNumbers": [c.phoneNumber for c in contacts],
                    "secondaryContactIds": [c.id for c in contacts if c.id != phonenumber_query[0].id]
                }})
            else:
                new = Contacts.objects.create(phoneNumber=phonenumber, linkPrecedence="primary")
                return JsonResponse({"contact": {
                    "primaryContactId": new.id,
                    "emails": [],
                    "phoneNumbers": [new.phoneNumber],
                    "secondaryContactIds": []
                }})

        return JsonResponse({"message":"Invalid JSON"}, status=400)
