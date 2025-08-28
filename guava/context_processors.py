def is_admin(request):
    return {'is_admin': request.user.groups.filter(name='admin').exists()}

def is_owner(request):
    return {'is_owner': request.user.groups.filter(name='owner').exists()}

def is_inspection(request):
    return {'is_inspection': request.user.groups.filter(name='inspection').exists()}

def is_production(request):
    return {'is_production': request.user.groups.filter(name='production').exists()}