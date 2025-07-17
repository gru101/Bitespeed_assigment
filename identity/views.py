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
    def post(self, request, *args, **kwargs):
        try: 
            data = json.loads(request.body)
        except:
            return JsonResponse(data={"message":"invalid json"})
                      
        email = data.get("email", None)
        phonenumber = data.get("phoneNumber", None)
        print(email, phonenumber)

        email_query = Contacts.objects.filter(email=email)
        phonenumber_query = Contacts.objects.filter(phoneNumber=phonenumber)
        or_query = Q(email=email) | Q(phoneNumber=phonenumber)  
        and_query = Q(email=email) & Q(phoneNumber=phonenumber)  

        if email is not None and phonenumber is None: 
            email=str(email).replace(" ","")
            if email_query.exists():
                record = email_query[0]
                return JsonResponse(data={"contact": {
                                            "primaryContactId": record.id,
                                            "emails" : [record.email],
                                            "phonenumber" : [record.phoneNumber],
                                            "secondaryContactId": []}
                                            })
            elif email_query.exists() is False:
                new_record = Contacts.objects.create(email=email, linkedId=None, linkPrecedence="primary")
                new_record.save()
                return JsonResponse(data={"contact": {
                                            "primaryContactId": new_record.id,
                                            "emails" : [new_record.email],
                                            "phonenumber" : [new_record.phoneNumber],
                                            "secondaryContactId": []}
                                            })
            
        elif phonenumber is not None and email is None: 
            phonenumber = str(phonenumber).replace(" ","")
            if phonenumber_query.exists():
                record = phonenumber_query[0]
                return JsonResponse(data={"contact": {
                                            "primaryContactId": record.id,
                                            "emails" : [record.email],
                                            "phonenumber" : [record.phoneNumber],
                                            "secondaryContactId": []}
                                            })
            elif phonenumber_query.exists() is False:
                new_record = Contacts.objects.create(phoneNumber=phonenumber, linkedId=None, linkPrecedence="primary")
                new_record.save()
                return JsonResponse(data={"contact": {
                                            "primaryContactId": new_record.id,
                                            "emails" : [new_record.email],
                                            "phonenumber" : [new_record.phoneNumber],
                                            "secondaryContactId": []}
                                            })
            
        elif email is not None and phonenumber is not None:
            if email_query.exists() and phonenumber_query.exists():
                if email_query[0].id != phonenumber_query[0].id:
                    #Take the one which is the most recently created and update its likedId with oldest contact id and its linkPrecedence to secondary.
                    if email_query[0].createdAt < phonenumber_query[0].createdAt:
                        phonenumber_query.update(linkedId=email_query[0].id, linkPrecedence="secondary")
                        return JsonResponse(data={"contact": {
                                                "primaryContactId": email_query[0].id,
                                                "emails" : [email_query[0].email, phonenumber_query[0].email],
                                                "phonenumber" : [email_query[0].phoneNumber, phonenumber_query[0].phoneNumber],
                                                "secondaryContactId": [phonenumber_query[0].id]}
                                                })
                    elif phonenumber_query[0].createdAt < email_query[0].createdAt:
                        email_query.update(linkedId=phonenumber_query[0].id, linkPrecedence="secondary")
                        return JsonResponse(data={"contact": {
                                                "primaryContactId": phonenumber_query[0].id,
                                                "emails" : [email_query[0].email, phonenumber_query[0].email],
                                                "phonenumber" : [email_query[0].phoneNumber, phonenumber_query[0].phoneNumber],
                                                "secondaryContactId": [phonenumber_query[0].id]}
                                                })
            elif email_query.exists() and phonenumber_query.exists() is False:
                Contacts.objects.create(phoneNumber=phonenumber, linkedId=email_query[0].id, linkPrecedence="secondary")
                records = Contacts.objects.filter(linkedId=email_query[0].id)
                return JsonResponse(data={"contact": {
                                                "primaryContactId": email_query[0].id,
                                                "emails" : [record.email for record in records],
                                                "phonenumber" : [record.phoneNumber for record in records],
                                                "secondaryContactId": [record.id for record in records if record.id != email_query[0].id]}})
            elif phonenumber_query.exists() and email_query.exists() is False:
                Contacts.objects.create(email=email, linkedId=phonenumber_query[0].id, linkPrecedence="secondary")
                records = Contacts.objects.filter(linkedId=phonenumber_query[0].id)
                return JsonResponse(data={"contact": {
                                                "primaryContactId": phonenumber_query[0].id,
                                                "emails" : [record.email for record in records],
                                                "phonenumber" : [record.phoneNumber for record in records],
                                                "secondaryContactId": [record.id for record in records if record.id != phonenumber_query[0].id]}})
            elif phonenumber_query.exists() is False and email_query.exists() is False:
                new_record = Contacts.objects.create(email=email,phoneNumber=phonenumber, linkPrecedence="primary")
                return JsonResponse(data={"contact": {
                                                "primaryContactId": new_record.id,
                                                "emails" : [new_record.email],
                                                "phonenumber" : [new_record.phoneNumber],
                                                "secondaryContactId": []}})
        return JsonResponse(data={"message":"Invalid JSON"},status=400)  
    
