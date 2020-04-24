from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView, RetrieveAPIView

from django.db.models import Q

from . import serializers as accounts_serializers
from . import models as accounts_models

from interests.tasks import  import_tweets_for_user, import_papers_for_user, update_short_term_interest_model_for_user


class RegisterView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        user_data = request.data
        user_data["username"] = user_data.get("email")
        serializer = accounts_serializers.UserRegistrationSerializer(data=user_data)
        serializer.is_valid(raise_exception=True)
        user = serializer.create(serializer.validated_data)
        user.set_password(serializer.validated_data["password"])
        user.save()
        import_tweets_for_user.delay(user.id)
        import_papers_for_user.delay(user.id)
        # extract keywords
        update_short_term_interest_model_for_user.s(user.id).apply_async(countdown=2 * 60)
        return Response(accounts_serializers.UserSerializer(instance=user).data)


class LoginView(APIView):
    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if email and password:
            user = accounts_models.User.objects.filter(email__iexact=email).first()
            if user and user.check_password(password):
                token, _ = Token.objects.get_or_create(user=user)
                response = accounts_serializers.UserSerializer(user).data
                response["token"] = token.key
                return Response(response)
        return Response(
            {"detail": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST
        )


class LogoutView(APIView):
    """
    Invalidate auth token
    """

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({})

class UserView(RetrieveUpdateAPIView):
    serializer_class = accounts_serializers.UserSerializer

    def get_object(self):
        return self.request.user


class UserSuggestionView(ListAPIView):
    serializer_class = accounts_serializers.UserSerializer

    def get_queryset(self):
        term = self.kwargs.get("query")
        return accounts_models.User.objects.filter(Q(email__icontains=term) | Q(first_name__icontains=term) | Q(last_name__icontains=term))


class PublicProfileView(RetrieveAPIView):
    serializer_class = accounts_serializers.UserSerializer
    queryset = accounts_models.User.objects.all()

    def get_serializer_context(self):
        return {"request": self.request}