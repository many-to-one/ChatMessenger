from django.shortcuts import get_object_or_404
from rest_framework import authentication
from rest_framework import exceptions
from uuid import uuid4
from django.utils import timezone
from datetime import timedelta
from rest_framework.exceptions import PermissionDenied

from users.models import BlackListToken, CustomUser


class CustomTokenAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):
        # Split the "Authorization" header into its components
        auth = authentication.get_authorization_header(request).split()
        print('AUTHENTICATION auth -----------------------------', auth)


        # Check if the request is a POST request to the 'login' endpoint
        if request.method == 'POST' and 'login' in request.path:

            # Generate a new token and associate it with the user's email
            token = f'{uuid4()}{uuid4()}{uuid4()}'
            email = request.data.get('email')
            user = get_object_or_404(CustomUser, email=email)

            # Return the user and the generated token
            return (user, token)
        

        # Check if the request is a POST request to the 'userToken' endpoint
        if request.method == 'POST' and 'accessToken' in request.path:

            # Generate a new token and associate it with the user's email
            token = f'{uuid4()}{uuid4()}{uuid4()}'
            id = request.data.get('userId')
            user = get_object_or_404(CustomUser, id=id)

            # Return the user and the generated token
            return (user, token)
        
        
        # Check if the request is a POST request to the 'login' endpoint
        elif request.method == 'POST' and 'register' in request.path:

            # Generate a new token and associate it with the user's email
            token = f'{uuid4()}{uuid4()}{uuid4()}'
            username = request.data.get('username')
            email = request.data.get('email')
            user = CustomUser.objects.create(
                username=username,
                email=email
                )
            user.save()

            # Return the user and the generated token
            return (user, token)
        


        # Check if the "Authorization" header contains a token with the "Bearer" prefix
        if auth and auth[0].lower() == b'bearer':

            # Ensure that the token header contains two components
            if len(auth) != 2:
                raise exceptions.AuthenticationFailed('Invalid token header')

            # Extract the token from the header and decode it
            token_bytes = auth[1]
            token = token_bytes.decode('utf-8')
            print('AUTHENTICATION -----------------------------', token)

            def get_object_or_403(model, **kwargs):
                try:
                    return model.objects.get(**kwargs)
                except model.DoesNotExist:
                    raise PermissionDenied("Object does not exist")  # 403 Permission Denied

            # Retrieve the user associated with the provided token with the custom function
            user = get_object_or_403(CustomUser, token=token)

            # Check if the token has been added to the blacklist (dead_token)
            dead_token = BlackListToken.objects.filter(token=token)
            if dead_token:
                print('dead_token -----------------------------', dead_token)
                # Clear the token if it's in the blacklist and return the user with an empty token
                token = ''
                return (user, token)

            if user:
                # Calculate the time elapsed since the user's last login
                time = timezone.now() - user.login_at

                # Check if the time elapsed is greater than 1 minute
                if time > timedelta(minutes=60):
                    print('timedelta > -------------------------')
                    # Add the token to the blacklist
                    BlackListToken.objects.create(
                        token=token,
                        user=user,
                    )

                    # Clear the token value for the user and log them out
                    user.token = ''
                    user.is_logged = False
                    user.save()
                    print('return (user, token) -------------------------')
                    return (user, user.token)

                # Return the user and the original token
                return (user, token)
        