from django.http import JsonResponse
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Package, UserPackage
from .forms import CustomUserCreationForm, UserProfileForm
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from requests.auth import HTTPBasicAuth
import datetime
import base64

logger = logging.getLogger(__name__)

# Safaricom API credentials (sandbox or live)
CONSUMER_KEY = 'NbOWGeZ1mjQlBtILhUZoWltCXD4DEGjPYpjwYmC1unADUtEV' 
CONSUMER_SECRET = 'ELSkcAFo4UHikX2jXbIT6pdAsMk0hbYqd3adsM4zzASgI55qAgQTkSECVKAWllII' 
BUSINESS_SHORT_CODE = "174379"  
LIPA_NA_MPESA_ONLINE_URL = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
API_BASE_URL = "https://sandbox.safaricom.co.ke"
VALIDATION_URL = "https://mydomain.com/validation"
CONFIRMATION_URL = "https://mydomain.com/confirmation"


def get_access_token():
    """Fetch access token for Safaricom API"""
    api_url = f'{API_BASE_URL}/oauth/v1/generate?grant_type=client_credentials'
    try:
        response = requests.get(api_url, auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET))
        if response.status_code == 200:
            access_token = response.json().get('access_token')
            if access_token:
                logger.info("Access token successfully retrieved.")
                return access_token
            else:
                raise ValueError("Access token not received.")
        else:
            logger.error(f"Failed to get access token. Status code: {response.status_code}, Response: {response.text}")
            raise ValueError(f"Error: {response.status_code}")
    except Exception as e:
        logger.error(f"Exception occurred while fetching access token: {e}")
        raise


def get_timestamp():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')


def generate_password(shortcode, passkey, timestamp):
    data_to_encode = shortcode + passkey + timestamp
    return base64.b64encode(data_to_encode.encode('utf-8')).decode('utf-8')


@login_required
def purchase_plan(request, package_id):
    """Handles the Lipa na M-Pesa Online payment process"""
    package = get_object_or_404(Package, id=package_id)

    if request.method == 'POST':
        phone_number = request.POST.get('254708374149')  

    
        passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
        callback_url = "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl"  # Provide your actual callback URL here
        timestamp = get_timestamp()
        password = generate_password(BUSINESS_SHORT_CODE, passkey, timestamp)


        access_token = get_access_token()  
        headers = {"Authorization": f"Bearer {access_token}"}

    #    600992
        payload = {
            "BusinessShortCode": "8074896",
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerBuyGoodsOnline",
            "Amount": "1",  
            "PartyA":"254704863390", 
            "PartyB": "",
            "PhoneNumber": "254704863390",
            "CallBackURL": callback_url,
            "AccountReference": "LipaMnet",  
            "TransactionDesc": "Test"
        }

        response = requests.post(LIPA_NA_MPESA_ONLINE_URL, json=payload, headers=headers)
        logger.info(f"STK Push Response: {response.text}")
        response_data = response.json()

        print("==================================================================================")
        print(response.text)

        if response_data.get('ResponseCode') == '0':
            messages.success(request, "Payment initiated successfully. Please check your phone to complete the transaction.")
            return redirect('dashboard')
        else:
            messages.error(request, f"Payment failed: {response_data.get('ResponseDescription', 'Unknown error.')}")

    return render(request, 'wifi/purchase_confirmation.html', {'package': package})


@csrf_exempt
def payment_callback(request):
    """Handle the callback from MPESA STK push"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.info(f"Received payment callback data: {data}")

            stk_callback = data.get('Body', {}).get('stkCallback', {})
            result_code = stk_callback.get('ResultCode')

            if result_code == 0:  # Successful transaction
                callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                amount = receipt_number = phone_number = None

                for item in callback_metadata:
                    if item['Name'] == 'Amount':
                        amount = item['Value']
                    elif item['Name'] == 'MpesaReceiptNumber':
                        receipt_number = item['Value']
                    elif item['Name'] == 'PhoneNumber':
                        phone_number = item['Value']

                logger.info(f"Parsed metadata - Amount: {amount}, Receipt: {receipt_number}, Phone: {phone_number}")

                user_package = UserPackage.objects.filter(user__profile__phone_number=phone_number).first()
                if user_package:
                    user_package.is_online = True
                    user_package.payment_status = "Completed"
                    user_package.mpesa_receipt = receipt_number
                    user_package.amount_paid = amount
                    user_package.save()

                return JsonResponse({"status": "Success", "message": "Payment processed successfully."})

            logger.error(f"Payment failed with ResultCode: {result_code}")
            return JsonResponse({"status": "Failed", "message": "Payment failed or was canceled."}, status=400)

        except json.JSONDecodeError:
            logger.error("Invalid JSON format received.")
            return JsonResponse({"status": "Error", "message": "Invalid JSON format."}, status=400)

    logger.error("Invalid request method.")
    return JsonResponse({"status": "Error", "message": "Invalid request method."}, status=400)


@login_required
def initiate_c2b_payment(request, package_id):
    """Initiate C2B Payment using PayBill for a selected package"""
    package = get_object_or_404(Package, id=package_id)

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number').replace("+", "").strip()
        amount = request.POST.get('amount')  

       
        access_token = get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        payload = {
            "ShortCode": BUSINESS_SHORT_CODE,
            "CommandID": "CustomerPayBillOnline",
            "Amount": amount,
            "Msisdn": 254703292479, 
            "BillRefNumber": "Test123"  
        }

      
        response = requests.post(LIPA_NA_MPESA_ONLINE_URL, json=payload, headers=headers)
        response_data = response.json()

        if response.status_code == 200 and response_data.get('ResponseCode') == '0':
            messages.success(request, "Payment initiated successfully.")
            return redirect('dashboard')
        else:
            logger.error(f"Payment failed: {response.text}")
            messages.error(request, "Payment initiation failed. Please try again.")

    return render(request, 'wifi/purchase_confirmation.html', {'package': package})


@csrf_exempt
def validation_url(request):
    """Handles payment validation for C2B"""
    if request.method == 'POST':
        data = json.loads(request.body)
        logger.info(f"Validation request received: {data}")

        response = {
            "ResultCode": 0,
            "ResultDesc": "Validation successful"
        }
        return JsonResponse(response)
    return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid request method"}, status=400)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  
            username = form.cleaned_data.get('username')
            phone_number = form.cleaned_data.get('phone_number')
            raw_password = form.cleaned_data.get('password1')
            
            user = authenticate(username=username, phone_number=phone_number, password=raw_password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Account created successfully for {username}!")
                return redirect('dashboard')  
        else:
            for msg in form.errors.values():
                messages.error(request, msg)
    else:
        form = CustomUserCreationForm()

    return render(request, 'wifi/register.html', {'form': form})

def register_success(request):
    return render(request, 'wifi/register_successful.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'wifi/login.html')

@login_required
def dashboard_view(request):
    packages = Package.objects.all()
    user_package = UserPackage.objects.filter(user=request.user).first()
    return render(request, 'wifi/dashboard.html', {
        'packages': packages, 
        'user_package': user_package,
    })

@login_required
def my_profile(request):
    return render(request, 'wifi/my_profile.html', {'user': request.user})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('my_profile')
        else:
            messages.error(request, 'Failed to update profile. Please check your details.')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'wifi/edit_profile.html', {'form': form})

@login_required
def change_password(request):
    return render(request, 'wifi/change_password.html')

@login_required
def purchase_plans(request):
    try:
        user_package = UserPackage.objects.get(user=request.user)
    except UserPackage.DoesNotExist:
        user_package = None

    packages = Package.objects.all()

    return render(request, 'wifi/purchase_plans.html', {
        'user_package': user_package,
        'packages': packages,
    })

def purchase_confirmation(request):
    return render(request, 'wifi/purchase_confirmation.html')

