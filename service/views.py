from __future__ import unicode_literals
from django.shortcuts import render, redirect
from django.http import HttpResponse
from background_task import background
from .forms import test_form
from . import models
import requests
import hashlib
import io,os
from zipfile import ZipFile
from django.conf import settings
from django.contrib import messages
from django.db import connection
from django.core.mail import send_mail
from service.sms import Sms
import random
from base64 import b64encode
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
import xml.etree.cElementTree as ET
import pyodbc

uidai_con = pyodbc.connect("DRIVER={SQL Server};SERVER=10.0.33.62,1433;DATABASE=uidai;UID=uidai;PWD=uidai")
uidai_cur = uidai_con.cursor()
cursor = connection.cursor()

def offline_ekyc(request):
    if request.POST:
        form = test_form(request.POST)
        if form.is_valid():
            aadhar_num = request.POST['aadhar_num']
            otp = random.randint(100000,999999)
            print("otp", otp)
            cursor.execute("INSERT INTO otp (aadhar_num, otp) VALUES ({},{})".format(aadhar_num, otp))
            cursor.execute("SELECT phone FROM details WHERE aadhar_num={}".format(aadhar_num))
            phone_number = cursor.fetchone()

            print(aadhar_num, phone_number[0])
            #send_sms = Sms('9121587454','Shiva@01')
            send_sms = Sms('8297235583','Shiva@01')
            send_sms.send(phone_number, str(otp))
            return render(request, 'offline_ekyc_otp.html', {'aadhar_num':aadhar_num})
    else:
        form = test_form()
    return render(request, 'offline_ekyc.html', {'form':form})


def offline_ekyc_otp(request):
    if request.POST:
        aadhar_num = request.POST['aadhar_num']
        verify_otp = request.POST['otp']
        share_code = request.POST['share_code']
        print("verify_otp", verify_otp)
        cursor.execute("SELECT  otp FROM otp WHERE aadhar_num={} ".format(aadhar_num))
        otp_fetch = cursor.fetchone()
        print("otp_fetch",otp_fetch[0])

        if int(verify_otp) == int(otp_fetch[0]):
            #cursor.execute("SELECT * FROM details FOR XML AUTO")
            cursor.execute("SELECT * FROM details WHERE aadhar_num={}".format(aadhar_num))
            xml = cursor.fetchone()
            print(xml)
            KYC = ET.Element("KYC")
            uidiadata = ET.SubElement(KYC, "uidiadata")

            ET.SubElement(uidiadata, "AadharNumber", name="aadhar Number").text = str(xml[0])
            ET.SubElement(uidiadata, "Name", name="Name").text = str(xml[1]) +str(xml[2]) +str(xml[3])
            ET.SubElement(uidiadata, "gender", name="gender").text = str(xml[4])
            ET.SubElement(uidiadata, "DOB", name="DOB").text = str(xml[7])
            ET.SubElement(uidiadata, "phone", name="phone").text = str(xml[9])
            ET.SubElement(uidiadata, "house", name="house").text = str(xml[11])
            ET.SubElement(uidiadata, "pincode", name="pincode").text = str(xml[12])
            ET.SubElement(uidiadata, "district", name="district").text = ""
            ET.SubElement(uidiadata, "state", name="state").text = ""
            ET.SubElement(uidiadata, "country", name="country").text = "India"

            tree = ET.ElementTree(KYC)
            fnm = "media/off_kyc/"+str(aadhar_num)
            tree.write("{}.xml".format(fnm))
            # download xml file



            # delete otp
            cursor.execute("DELETE FROM otp WHERE aadhar_num={}".format(aadhar_num))
            return render(request, 'off_kyc_download.html', {"file":fnm})

        else:
            return HttpResponse("invalid otp") # redirect back



def verify_mobile_mail(request):
    if request.POST:
        form = test_form(request.POST)
        if form.is_valid():
            if 'email' in request.POST:
                aadhar_num = request.POST['aadhar_num']
                email = request.POST['email']
                otp = (random.randint(100000,999999))
                print(otp)
                #otp = hashlib.sha256((random.randint(100000,999999)).encode())
                cursor.execute("INSERT INTO otp (aadhar_num, otp) VALUES ({},{})".format(aadhar_num, otp))
                cursor.execute("SELECT phone FROM details WHERE aadhar_num={} AND email='{}'".format(aadhar_num, email))
                phone_number = cursor.fetchone()

                #send_sms = Sms('9121587454','Shiva@01')
                send_sms = Sms('8297235583','Shiva@01')
                send_sms.send(phone_number, str(otp))

                return render(request, 'verify_otp.html', {'aadhar_num':aadhar_num, 'email':email})

            if 'number' in request.POST:
                aadhar_num = request.POST['aadhar_num']
                mobile = request.POST['number']

                otp = (random.randint(100000,999999))
                print(otp)
                cursor.execute("INSERT INTO otp VALUES ({},'{}')".format(aadhar_num, otp))
                cursor.execute("SELECT  phone FROM details WHERE aadhar_num AND phone={}".format(aadhar_num, mobile))
                phone_number = cursor.fetchone()

                #send_sms = Sms('9121587454','Shiva@01')
                send_sms = Sms('8297235583','Shiva@01')
                send_sms.send(phone_number, str(otp))

                return render(request, 'verify_otp.html', {'aadhar_num':aadhar_num, 'number':mobile})

    else:
        form = test_form()
    return render(request, 'verify_mobile_email.html', {'form':form})

def verify_otp(request):
    if request.POST:
        otp = request.POST['otp']
        print(request.POST)
        if 'email' in request.POST and request.POST['email']!='':
            aadhar_num = request.POST['aadhar_num']
            email =request.POST['email']
            print(aadhar_num, email)
            cursor.execute("SELECT  otp FROM otp WHERE aadhar_num={} ".format(aadhar_num))
            otp_fetch = cursor.fetchone()
            print(otp_fetch[0])

            if int(otp) == int(otp_fetch[0]):
                print("request:",request.POST)
                cursor.execute("DELETE FROM otp WHERE aadhar_num={}".format(aadhar_num))
                return render(request, 'verified_mobile_email.html', {'verify_email': 1,'email':email,'msg':'email linked to aadhar'})
            else:
                cursor.execute("DELETE FROM otp WHERE aadhar_num={}".format(aadhar_num))
                return render(request, 'verified_mobile_email.html', {'verify_email': 1,'email':email,'msg':'This email not linked to aadhar'})

        if 'number' in request.POST and request.POST['number']!='':
            aadhar_num = request.POST['aadhar_num']
            number = request.POST['number']
            print(aadhar_num, number)
            cursor.execute("SELECT  otp FROM otp WHERE aadhar_num={} ".format(aadhar_num))
            otp_fetch = cursor.fetchone()

            if int(otp) == int(otp_fetch[0]):
                print("request:",request.POST)
                cursor.execute("DELETE FROM otp WHERE aadhar_num={}".format(aadhar_num))
                verify =False
                return render(request, 'verified_mobile_email.html', {'verify_mobile': 1,'mobile':number,'msg':'This number is linked to aadhar'})
            else:
                cursor.execute("DELETE FROM otp WHERE aadhar_num={}".format(aadhar_num))
                verify =False
                return render(request, 'verified_mobile_email.html', {'verify_mobile': 1,'mobile':number,'msg':'This number is not linked to aadhar'})
    else:
        return HttpResponse("Invalid request")



def verify_aadhar(request):
    if request.method == 'POST':
        form = test_form(request.POST)
        if form.is_valid():
            Aadhar_num = request.POST['aadhar_num']
            print(Aadhar_num)
            cursor.execute("SELECT aadhar_num, gender, date_of_birth FROM details WHERE aadhar_num = {}".format(Aadhar_num))
            aadhar_check = cursor.fetchone()
            return HttpResponse(aadhar_check)
        else:
            return HttpResponse("form invalid")
    else:
        form = test_form()
    return render(request, 'verify_aadhar.html', {'form':form})



def update_verify(request):
    cursor.execute("SELECT * FROM update_details")
    update_verify_result = cursor.fetchall()

    print(update_verify_result)

    return render(request, 'update_verify.html', {'update_verify_result':update_verify_result})


def get_update_status(request):
    if request.POST:
        form = test_form(request.POST)
        if form.is_valid():
            human = True
            enrolled_id = request.POST['enrolled_ID']
            #enrolled_time = request.POST['Enrolled_Time']
            print(enrolled_id)
            cursor.execute("SELECT aadhar_num FROM enrolled WHERE EXISTS (SELECT enroll_id,enroll_time FROM enrolled WHERE enroll_id = {} AND enroll_time = {})".format(enrolled_id,enrolled_time))
            update_status = cursor.fetchone()
            print(update_status)
            return HttpResponse("sucess")
            #return render(request, 'update_status.html',{'form':form})
        else:
            return HttpResponse("form invaild")
    else:
        form = test_form()

    return render(request, '1.html', {'form':form})

def complaint_front(request):
    return render(request, 'complaint.html')

def complaint(request):
    if request.POST:
        form = test_form(request.POST)
        if form.is_valid():
            aadhar_num = request.POST["enroll_ID"]
            name = request.POST['Name']
            email = request.POST['Email']
            phone_no = request.POST['Phone_No']
            pinCode = request.POST["pin_Code"]
            city = request.POST["city"]
            #comp_type = request.POST['select1']
            category = request.POST['select2']
            remark = request.POST['Remarks']
            #complaint_id = uidai_cur.execute("SELECT [dbo].[complaint_id_gen]()").fetchall()[0][0]
            complaint_id = 23
            # date time
            #print(aadhar_num, name, email, phone_no, pinCode, city, comp_type, category, remark)
            cursor.execute("INSERT INTO complaints VALUES ({},{},'{}','{}',{},{},'{}','{}','{}')".format(complaint_id, aadhar_num, name, email, phone_no, pinCode, city, category, remark))
            #cursor.execute("INSERT INTO complaint_status (complaint_id, status) VALUES ({},'{}')".format(complaint_id, "In Progress"))

            #send_sms = Sms('9121587454','Shiva@01')
            send_sms = Sms('8297235583','Shiva@01')
            send_sms.send(phone_no, 'Your complaint ID:'+ str(complaint_id) + ",please verify your complaint status with this id")

            send_mail('Complaint',remark,'ruthala.shiva5128@gmail.com',['ruthala.shiva5128@gmail.com'],fail_silently=False,)
            send_mail('Complaint Number','Your complaint ID:'+ str(complaint_id) + ",please verify your complaint status with this id",'ruthala.shiva5128@gmail.com',[email],fail_silently=False,)

            return HttpResponse("complained received")
        else:
            return HttpResponse("invalid captcha")
    else:
        form = test_form()
        return render(request, '2.html',{'form':form})
# auto chek enrollment id exists or not
def check_enroll_id(request):
    if request.method == "GET":
        raise Http404("URL doesn't exists")
    else:
        response_data = {}
        enrollment_id = request.POST["enroll_ID"]
        user = None
        try:
            try:
                cursor.execute("(SELECT 1 FROM aadhar_num WHERE aadhar_num={})".format(enrollment_id))
                result_set = cursor.fetchall()
                if result_set:
                    user = True
            except ObjectDoesNotExist as e:
                pass
            except Exception as e:
                raise e
            if not user:
                response_data["is_success"] = True
            else:
                response_data["is_success"] = False
        except Exception as e:
            response_data["is_success"] = False
            response_data["msg"] = "Some error occurred. Please let Admin know."

        return JsonResponse(response_data)

# autofill city/state/district/country
def autofill1_check(request):
    if request.method == "GET":
        raise Http404("URL doesn't exists")
    else:
        response_data = {}
        pinCode = request.POST["pin_Code"]
        user = None
        try:
            try:
                if len(str(pinCode)) == 6:
                    user = True
                    pre_url = 'http://postalpincode.in/api/pincode/'
                    url = pre_url + str(pinCode)
                    resp = requests.get(url=url)
                    data = resp.json()

                    response_data["is_sucess"] = True
                    response_data["Region"] =data['PostOffice'][0]['Region']
                    #response_data["State"] = data['PostOffice'][0]['State']
                    #response_data["Country"] = data['PostOffice'][0]['Country']
            except ObjectDoesNotExist as e:
                pass
            except Exception as e:
                raise e
            if not user:
                response_data["is_sucess"] = False

        except Exception as e:
            response_data["is_sucess"] = False
            response_data["msg"] = "Some error occurred. Please let Admin know."

        return JsonResponse(response_data)

def complaint_status(request):
    if request.method == 'POST':
        form = test_form(request.POST)
        if form.is_valid():
            enrolled_id = request.POST['enrolled_ID']
            cursor.execute("SELECT complaint_id, reply, status FROM complaint_status WHERE complaint_id = {}".format(enrolled_id))
            Complaint_result = cursor.fetchone()
            # get complaint for complaint id
            if Complaint_result[2] == "success":
                status = True
            else:
                status = False
            return render(request, 'complaint_status_result.html',{'Complaint_id':Complaint_result[0],'Complaint_reply':Complaint_result[1],'Complaint_status':Complaint_result[2],'status':status})
        else:
            return HttpResponse("complained not received")
    else:
        form = test_form()
    return render(request, 'complaint_status.html',{'form':form})

def address_status(request):
    if request.method == "POST":
        form = test_form(request.POST)
        if form.is_valid():
            human = True
            aadhar_num = request.POST['aadhar_num']

            cursor.execute("SELECT aadhar_num, address_status FROM update_status WHERE aadhar_num={}".format(aadhar_num))
            status = cursor.fetchone()
            print(status)
            cursor.execute("SELECT res_address, pincode FROM details WHERE aadhar_num={}".format(aadhar_num))
            update_details = cursor.fetchone()
            print(update_details)

            if status[1] == 'Accepted':
                verify = True
            else:
                verify = False

            return render(request, 'address_status_result.html', {'verify':verify,'msg':"Address updated",'msg1':"Address not updated",'status':status,'update_details':update_details})
    else:
        form  = test_form()
    return render(request, 'address_status.html', {'form':form})

def address_status_result(request):
    pass

def bank_linking(request):
    if request.method == "POST":
        print("hello")
        form = test_form(request.POST)
        if form.is_valid():
            print("Working")
            aadhar_num = request.POST['aadhar_num']
            otp = (random.randint(100000,999999))
            print(otp)
            #otp = hashlib.sha256((random.randint(100000,999999)).encode())
            cursor.execute("INSERT INTO otp (aadhar_num, otp) VALUES ({},{})".format(aadhar_num, otp))
            return render(request, 'bank_link_otp.html', {'aadhar_num':aadhar_num})
    else:
        print("trying")
        form = test_form()
    print("not Working")
    return render(request, 'bank_link_verify.html', {'form':form})

def bank_linking_otp(request):
    if request.method == "POST":
        aadhar_num = request.POST['aadhar_num']
        otp = request.POST['otp']

        cursor.execute("SELECT  otp FROM otp WHERE aadhar_num={} ".format(aadhar_num))
        otp_fetch = cursor.fetchone()

        if int(otp) == int(otp_fetch[0]):
            cursor.execute("DELETE FROM otp WHERE aadhar_num={}".format(aadhar_num))
            print(aadhar_num)
            uidai_cur.execute("SELECT * FROM bank_details WHERE aadhar_num = {};".format(aadhar_num))
            details = uidai_cur.fetchall()

            return render(request, 'bank_link_status.html', {'details':details})

        return render(request, 'bank_link_otp.html', {'aadhar_num':aadhar_num})
    else:
        return redirect('{% url "service:bank_linking" %}')
