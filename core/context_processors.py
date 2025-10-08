from core.models import UserNotification

def notification_count(request):
    if request.session.get('user_id'): 
        user_id = request.session.get('user_id')
        count = UserNotification.objects.filter(user_id=user_id, is_read=False).count()
    else:
        count = 0
    return {'notification_count': count}