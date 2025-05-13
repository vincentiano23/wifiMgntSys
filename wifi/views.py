
from django.http import JsonResponse
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Package, UserPackage
from .forms import CustomUserCreationForm, UserProfileForm
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from requests.auth import HTTPBasicAuth
import datetime
from .utils import configure_router
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
import base64
from django.shortcuts import render
from librouteros import connect



logger = logging.getLogger(__name__)

def configure_router(data):
    """
    Utility function to configure the MikroTik router.
    Connects to the router and applies the configuration.
    """
    try:
        # Establish a connection with the router
        connection = connect(
            host=data["host"],
            username=data["username"],
            password=data["password"]
        )
        # Access the RouterOS API
        api = connection(cmd="/ip/address/add", address=data["src_address"])
        return "Router configured successfully."
    except Exception as e:
        logger.error(f"Error configuring router: {e}")
        raise Exception("Failed to configure the router. Please check the credentials and network settings.")

def router_configuration(request):
    """
    View to handle MikroTik router configuration.
    Accepts POST data and calls the utils function to configure the router.
    """
    if request.method == "POST":
        # Collect data from the form
        router_ip = request.POST.get("router_ip")
        username = request.POST.get("username", "admin")  # Default username
        password = request.POST.get("password", "")       # Ensure password is not hardcoded
        src_address = request.POST.get("src_address", "192.168.20.1/24")  # Default source address

        # Prepare data dictionary
        data = {
            "host": router_ip,
            "username": username,
            "password": password,
            "src_address": src_address,
        }

        try:
            # Call the utility function to configure the router
            message = configure_router(data)
            messages.success(request, message)
        except Exception as e:
            messages.error(request, f"Router configuration failed: {e}")
        
        return redirect("dashboard")  # Redirect back to the dashboard

    # Render the router configuration form
    return render(request, "wifi/router_config.html")

   

consumer_key = 'NbOWGeZ1mjQlBtILhUZoWltCXD4DEGjPYpjwYmC1unADUtEV'  
consumer_secret = 'ELSkcAFo4UHikX2jXbIT6pdAsMk0hbYqd3adsM4zzASgI55qAgQTkSECVKAWllII'  
api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

def get_access_token():
    response = requests.get(api_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception("Failed to get access token")

   

def generate_password(shortcode, passkey, timestamp):
    data_to_encode = shortcode + passkey + timestamp
    return base64.b64encode(data_to_encode.encode('utf-8')).decode('utf-8')


def get_timestamp():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')

def stk_push_customer_buy_goods(phone_number, amount):
    # Safaricom test credentials (Sandbox)
    business_short_code = "174379" 
    passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
    lipa_na_mpesa_online_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    callback_url = "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl"  
    timestamp = get_timestamp()
    password = generate_password(business_short_code, passkey, timestamp)

    # Fetch access token
    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    
    payload = {
        "BusinessShortCode":  "174379",
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerBuyGoodsOnline", 
        "Amount": "1",
        "PartyA": "254742463773",
        "PartyB": "174379", 
        "PhoneNumber": "254703292479", 
        "CallBackURL": callback_url,
        "AccountReference": "TestBuyGoods",
        "TransactionDesc": "LipaMnet"
    }

    
    response = requests.post(lipa_na_mpesa_online_url, json=payload, headers=headers)

    response_data = response.json()
    print(response_data)
    return response_data


def purchase_plan(request, package_id):
 
    package = get_object_or_404(Package, id=package_id)

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')

        # Your STK push implementation here
        # For example:
        response = stk_push_customer_buy_goods(phone_number, package.price)

        # Check response and handle messages
        if response.get('ResponseCode') == '0':
            messages.success(request, "Payment initiated successfully. Please check your phone to complete the transaction.")
            return redirect('dashboard')
        else:
            messages.error(request, "Payment failed: " + response.get('ResponseDescription', 'Unknown error.'))

    return render(request, 'wifi/purchase_confirmation.html', {'package': package})


@login_required
def purchase_goods(request, amount):
    phone_number = request.POST.get('phone_number')

    if request.method == 'POST':
        try:
            response_data = stk_push_customer_buy_goods(phone_number, amount)
            if response_data.get('ResponseCode') == '0':
                messages.success(request, "Payment initiated successfully. Please check your phone to complete the transaction.")
                return redirect('dashboard')
            else:
                messages.error(request, "Payment failed: " + response_data.get('ResponseDescription', 'Unknown error.'))
        except Exception as e:
            messages.error(request, f"Error initiating payment: {e}")

    return render(request, 'wifi/purchase_confirmation.html')

@csrf_exempt
def payment_callback(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.info(f"Received payment callback data: {data}")

            stk_callback = data.get('Body', {}).get('stkCallback', {})
            result_code = stk_callback.get('ResultCode')

            if result_code == 0:  # Successful transaction
                callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                amount = None
                receipt_number = None
                phone_number = None

                for item in callback_metadata:
                    if item['Name'] == 'Amount':
                        amount = item['Value']
                    elif item['Name'] == 'MpesaReceiptNumber':
                        receipt_number = item['Value']
                    elif item['Name'] == 'PhoneNumber':
                        phone_number = item['Value']

                # Process successful payment here, e.g., update order status
                logger.info(f"Payment successful - Amount: {amount}, Receipt: {receipt_number}, Phone: {phone_number}")

                return JsonResponse({"status": "Success", "message": "Payment processed successfully."})

            logger.error(f"Payment failed with ResultCode: {result_code}")
            return JsonResponse({"status": "Failed", "message": "Payment failed or was canceled."}, status=400)

        except json.JSONDecodeError:
            logger.error("Invalid JSON format received.")
            return JsonResponse({"status": "Error", "message": "Invalid JSON format."}, status=400)

    logger.error("Invalid request method.")
    return JsonResponse({"status": "Error", "message": "Invalid request method."}, status=400)


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
                return redirect('login')  
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
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
             user = form.save()
             update_session_auth_hash(request, user)
             messages.success(request,"your password has been changed successfully")
             return redirect('wifi/change_password_successful.html')
            
        else:
           
            messages.error(request, "please correct the errors below")
            print("Form errors:", form.errors)
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'wifi/change_password.html')

def change_password_successful(request):
    return render(request,'wifi/change_password_successful.html')

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


def logout_view(request):
    logout(request)
    return redirect('login')