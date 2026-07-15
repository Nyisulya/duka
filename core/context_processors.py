def store_context(request):
    """
    Inapitisha object ya 'store' (Duka) kwenye templates zote kiotomatiki
    ikiwa request.duka ipo (kwa mujibu wa middleware yetu).
    """
    return {
        'store': getattr(request, 'duka', None)
    }
