'''
'''

class ValidationError (Exception):
    '''
    A private class for use in validators.py. Used to make writing validators shorter.
    '''
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

def ReturnValidAndErrorMessage(validator):
    '''
    ReturnValidAndErrorMessage is a decorator which catches ValidationError and returns
    a tuple (valid, err_msg) where valid is True if the argument is valid and False otherwise.
    If valid is False, a user-visible message is contained in err_msg
    ''' 
    def new_validator(request):
        valid = False
        err_msg = ""
        try:
            validator(request)
            valid = True
        except ValidationError as ve:
            err_msg = ve.msg
        return (valid, err_msg)
    return new_validator
            
@ReturnValidAndErrorMessage
def valid_customer_creation_parameters(request):
    params = request.POST
    if 'name' not in params:
        raise ValidationError('Please specify a name for the party.')
    elif 'party_size' not in params:
        raise ValidationError('Please specify a size of the party.')
    party_size = params['party_size']
    if party_size is "":
        raise ValidationError('Please specify a size of the party.')
    try:
        party_size = int(party_size)
    except ValueError:
        raise ValidationError('Party size must be a number.')
    if party_size < 1:
        raise ValidationError("%d is too small a party to put in this system." % party_size)
    if party_size > 999:
        raise ValidationError("Party of %d! That's a lot. Restaurants that can seat more than 999 people are not supported by this system." % party_size)
        