from django.contrib.auth import views as auth_views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    
    path('', views.register, name='register'),
    path('register-success/', views.register_success, name='register_success'),
    path('login/', views.login_view, name='login'),

  
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='wifi/password_reset.html'), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='wifi/password_reset_done.html'), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='wifi/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(template_name='wifi/password_reset_complete.html'), name='password_reset_complete'),

    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('my-profile/', views.my_profile, name='my_profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='password_change'),
    path('change-password-successful/', views.change_password_successful,name='change_password_successful'),
    path('router-config/', views.router_configuration, name='router_configuration'),

    path('purchase/<int:package_id>/', views.purchase_plan, name='purchase_plan'),
    path('purchase-confirmation/', views.purchase_confirmation, name='purchase_confirmation'),
    path('purchase-plans/', views.purchase_plans, name='purchase_plans'),

    # path('payment_issue/',views.paymet_issue, name= "payment_issue"),


    path('payment-callback/', views.payment_callback, name='payment_callback'),
    path('purchase-plans/', views.purchase_plans, name='purchase_plans'),
    path('logout/', views.logout_view, name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)