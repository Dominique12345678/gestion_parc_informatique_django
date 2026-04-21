from django.contrib.auth.decorators import user_passes_test

def verified_required(function=None, redirect_field_name='next', login_url='verify_otp'):
    """Vérifie que l'utilisateur a passé la vérification OTP"""
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_authenticated and (u.is_verified or u.is_admin() or u.is_superuser),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def admin_required(function=None, redirect_field_name='next', login_url='home'):
    """Vérifie que l'utilisateur est un ADMIN et est vérifié"""
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_authenticated and (u.is_admin() or u.is_superuser),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def technician_required(function=None, redirect_field_name='next', login_url='home'):
    """Vérifie que l'utilisateur est un TECHNICIAN ou ADMIN et est vérifié"""
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_authenticated and (u.is_verified or u.is_admin() or u.is_superuser) and (u.is_technician() or u.is_admin() or u.is_superuser),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
